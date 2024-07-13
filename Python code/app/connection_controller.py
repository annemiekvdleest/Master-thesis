import asyncio
import copy
import json
import os
import wave
from datetime import datetime, timedelta
from enum import Enum

import aiohttp
import dotenv
import pandas as pd
import pyaudio
import websockets
from openai import AsyncOpenAI

from generators import gpt, simple, action, emote

dotenv_file = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_file)

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 9
WAVE_OUTPUT_FILENAME = "output.wav"


class ServerMode(str, Enum):
    PRODUCTION = "PRODUCTION"
    TEST = "TEST"
    DEVELOP = "DEVELOP"


class CommunicationChannel(str, Enum):
    LIZZ_API = "LIZZ_API"
    EXTERNAL = "EXTERNAL"
    QUART_SERVER = "QUART SERVER"
    QUART_SOCKET = "QUART SOCKET"
    OPENAI_API = "OPENAI_API"

    def __str__(self):
        return str(self.value).lower()


class ConnectionStatus(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"

    def __str__(self):
        return str(self.value).lower()


class RequestStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PENDING = "PENDING"
    FAILED = "FAILED"

    def __str__(self):
        return str(self.value).lower()


class WeatherRequest(str, Enum):
    NOW = "NOW"
    FORECAST = "FORECAST"

    def __str__(self):
        return str(self.value).lower()


class RequestAppend(str, Enum):
    WEATHER = "_weather_"
    CALENDAR = "_calendar_"
    REPORT = "_report_"
    NEWS = "_news"

    def __str__(self):
        return str(self.value).lower()


class RequestPrepend(str, Enum):
    GEOCODE = "geocode_"

    def __str__(self):
        return str(self.value).lower()


def _get_server_id():
    server_id = ""
    try:
        server_id = os.getenv("SERVER_ID")
    except Exception as e:
        print("[" + CommunicationChannel.LIZZ_API + "] No stored server ID found, requesting a new one.")
    return server_id


def _save_server_id(server_id: str):
    global dotenv_file
    dotenv.set_key(dotenv_file, "SERVER_ID", server_id)


def _get_tablet_id():
    server_id = ""
    try:
        server_id = os.getenv("TABLET_ID")
    except Exception as e:
        print("[" + CommunicationChannel.LIZZ_API + "] No stored tablet ID found, requesting a new one.")
    return server_id


def _save_tablet_id(tablet_id: str):
    global dotenv_file
    dotenv.set_key(dotenv_file, "TABLET_ID", tablet_id)


def _get_dev_list():
    _dev_list = []
    try:
        with open("dev-list.json", "r") as f:
            _dev_list = [x["tablet_id"] for x in json.loads(f.read())]
    except Exception as e:
        print("[" + CommunicationChannel.LIZZ_API + "] No stored ID found, requesting a new one.")
    return _dev_list


class ConnectionController(object):

    def __init__(self, app):
        self._parent_app = app
        self.mode = ServerMode(os.getenv("SERVER_MODE"))
        self._dev_list = _get_dev_list()

        self._lizz_api_ws = None  # websocket connection will be established with the connect_websocket_as_server function
        self._lizz_tablet_ws = None  # websocket connection will be established with the connect_websocket_as_tablet function
        self._external_api = None  # http request session will be established with the connect_external function
        self._openai_api = None  # client for the openai chatgpt requests will be established with the connect_openai function
        self._connected_tablets = {}  # Used to track connection status of connected tablets {tablet_id : status}
        self._data_queue = {}  # Used to track incoming responses to our requests {request_id : response}
        self._gpt_history = {}  # Used to track history from gpt conversation

        self.history_df = pd.DataFrame(
            columns=["channel", "user_id", "tablet_id", "user_message", "assistant_output", "timestamp",
                     "processing_time"])

    def save_to_history(self, channel: str, user="", tablet="", message_in="", message_out="",
                        start_time: datetime = None):
        """
        Save to message history
        """
        now = datetime.utcnow()
        if not start_time:
            start_time = now
        processing_time = now - start_time
        new_record = pd.DataFrame(
            data={"channel": channel,
                  "user_id": user,
                  "tablet_id": tablet,
                  "user_message": message_in,
                  "assistant_output": message_out,
                  "timestamp": now,
                  "processing_time": processing_time}, index=[1])

        self.history_df = pd.concat([self.history_df, new_record], ignore_index=True)

    def dump_history(self):
        now = datetime.utcnow().strftime("%d-%m-%Y %H-%M-%S")
        self.history_df.to_csv("logs/" + now + ".log", sep="\t")
        print("[" + CommunicationChannel.QUART_SERVER + "] Wrote message history to 'logs/" + now + ".log'")

    async def _handle_request(self, msg: str):
        data = json.loads(msg)

        if data["client"]["type"] != "TABLET":
            return

        start_time = datetime.utcnow()
        tablet_id = data["client"]["id"]

        user_id = ""
        if "data" in data and "user" in data["data"] and "id" in data["data"]["user"]:
            user_id = data["data"]["user"]["id"]

        if self.mode != ServerMode.DEVELOP:
            if tablet_id in self._dev_list:
                return
        elif tablet_id not in self._dev_list:
            return

        """
        Process messages related to connection status
        """
        if data["type"] == "disconnected":
            self._connected_tablets[tablet_id] = ConnectionStatus.DISCONNECTED
            self.save_to_history(channel=CommunicationChannel.LIZZ_API, user=user_id, tablet=tablet_id,
                                 message_in="tablet_disconnected",
                                 message_out="", start_time=start_time)
            return

        elif (tablet_id not in self._connected_tablets or
              self._connected_tablets[tablet_id] is not ConnectionStatus.CONNECTED):
            self._connected_tablets[tablet_id] = ConnectionStatus.CONNECTED
            print("[" + CommunicationChannel.LIZZ_API + " (IN)] Connected with tablet with id " + tablet_id)
            self.save_to_history(channel=CommunicationChannel.LIZZ_API, user=user_id, tablet=tablet_id,
                                 message_in="tablet_connected",
                                 message_out="", start_time=start_time)

        """
        Process messages related to conversation
        """
        if data["type"] == "non-empathic-starter":
            return await self._respond(msg=simple.get_non_empathic_starter(tablet_id),
                                       channel=CommunicationChannel.LIZZ_API)

        if data["type"] == "basic-empathy-starter":
            self._gpt_history = {}
            return await self._respond(msg=gpt.get_basic_empathy_starter(tablet_id),
                                       channel=CommunicationChannel.LIZZ_API)

        if data["type"] == "rich-empathy-starter":
            self._gpt_history = {}
            return await self._respond(msg=gpt.get_rich_empathy_starter(tablet_id),
                                       channel=CommunicationChannel.LIZZ_API)

        if data["type"] == "external_interaction_response":
            if data["data"]["buttonPressed"]["value"] != "finish-conversation":
                audio = await self.listen_to_audio()
                tablet = data["client"]["id"]
                message_data = {"message": "...",
                                "messageTts": "   ",
                                "message_id": "is-typing",
                                "buttons": [],
                                "extra": json.dumps(emote.get_emotes_from_keys({})),
                                "listen": "manual"}
                outgoing_message = {"type": "external_interaction_message",
                                    "data": message_data,
                                    "client": data["client"]}
                await self._lizz_api_ws.send(json.dumps(outgoing_message))  # first queue the message
                await self.show_dialogue_screen(tablet)  # if that was successful, show the dialogue screen
                message_text = await self.transcribe_with_whisper(audio)
                if data["data"]["message"]["data"]["message_id"] in ["rich-empathy-conversation",
                                                                     "basic-empathy-conversation"]:
                    responseButton = {"value": data["data"]["buttonPressed"]["value"],
                                      "label": message_text}
                else:
                    responseButton = {"value": data["data"]["buttonPressed"]["value"],
                                      "label": data["data"]["buttonPressed"]["label"]}
            else:
                responseButton = {"value": data["data"]["buttonPressed"]["value"],
                                  "label": data["data"]["buttonPressed"]["label"]}
            response = data["data"]["message"]
            response["data"]["responseButton"] = responseButton
            if responseButton["value"] == "finish-conversation":
                response["data"]["message_id"] = "conversation"  # stop using chat-gpt
            response["type"] = "external_interaction_response"
            return await self._handle_conversation_request(response)

        elif "data" in data and "message_id" in data["data"] and data["data"]["message_id"] in \
                ["rich-empathy-conversation", "basic-empathy-conversation", "conversation"]:
            return await self._handle_conversation_request(data)

        elif "data" in data and "message_id" in data["data"] and data["data"]["message_id"] == "conversation-end":
            return await self._handle_conversation_end(data)

        """
        Process messages related to data
        """
        if data["type"] == "tablet_user_data":
            return await self._handle_data_response(data=data)
        elif data["type"] == "tablet_user_calendar":
            return await self._handle_calendar_response(data=data)
        elif data["type"] == "tablet_reports_and_configurations":
            return await self._handle_report_response(data=data)

        """
        Process error messages
        """
        if data["type"] == "error":
            print(
                "[" + CommunicationChannel.LIZZ_API + " (IN)] Received an error message from the server:" + msg)
            self.save_to_history(channel=CommunicationChannel.LIZZ_API, user=user_id, tablet=tablet_id,
                                 message_in=data["type"] + "_" + str(data["statusCode"]),
                                 message_out=data["message"], start_time=start_time)

    async def _listen_for_requests(self, interval=0.1):
        while True:
            if self._lizz_api_ws is not None:
                msg = await self._lizz_api_ws.recv()
                self._parent_app.add_background_task(self._handle_request, msg)

            await asyncio.sleep(interval)

    async def connect_open_ai(self):
        print("[" + CommunicationChannel.OPENAI_API + "] Establishing GPT client...")
        self._openai_api = AsyncOpenAI(api_key=os.environ.get("OPEN_AI_KEY"))
        print("[" + CommunicationChannel.OPENAI_API + "] Successfully established GPT client, ready for completion!")

    async def connect_external(self, interval=60):
        print("[" + CommunicationChannel.EXTERNAL + "] Opening session for external requests...")
        async with aiohttp.ClientSession() as session:
            self._external_api = session
            print("[" + CommunicationChannel.EXTERNAL + "] Ready to send external requests!")
            while True:
                await asyncio.sleep(interval)

    async def connect_to_socket_as_server(self, address, interval=60):
        print("[" + CommunicationChannel.LIZZ_API + "] Connecting to LIZZ API as 'java' server...")

        connect_line = address + "/?type=JAVA"
        iot_id = _get_server_id()
        if iot_id:
            connect_line += "&id=" + iot_id
        async with websockets.connect(connect_line) as websocket_:
            connect_msg = await websocket_.recv()
            data = json.loads(connect_msg)
            if data["type"] == "connected":
                iot_id = data["client"]["id"]

            self._lizz_api_ws = websocket_
            print("[" + CommunicationChannel.LIZZ_API + "] Successfully connected to LIZZ API! Server ID is " + iot_id)
            _save_server_id(iot_id)

            print("[" + CommunicationChannel.LIZZ_API + "] Now listening for responses...")
            while True:
                await asyncio.sleep(interval)  # we are not actually looking to respond to any messages as a 'tablet'

    async def connect_to_socket_as_tablet(self, address):
        print("[" + CommunicationChannel.LIZZ_API + "] Connecting to LIZZ API as 'tablet'...")

        connect_line = address + "/?type=TABLET"
        iot_id = _get_tablet_id()
        if iot_id:
            connect_line += "&id=" + iot_id
        async with websockets.connect(connect_line) as websocket_:
            connect_msg = await websocket_.recv()
            data = json.loads(connect_msg)
            if data["type"] == "connected":
                iot_id = data["client"]["id"]

            self._lizz_tablet_ws = websocket_
            print("[" + CommunicationChannel.LIZZ_API + "] Successfully connected to LIZZ API! Tablet ID is " + iot_id)
            _save_tablet_id(iot_id)
            await self._listen_for_requests()  # This while True loop will take it from here

    async def _get_report_defaults(self, tablet_id: str):
        start_time = datetime.utcnow()
        time_string = start_time.strftime("%Y-%m-%dT%H:%M:%S")

        client_data = await self.get_client_data(tablet_id)
        user_data = {"id": int(client_data["CLIENT-ID"])}
        message_data = {
            "type": "",
            "user": user_data,
            "response": ""
        }
        outgoing_message = {"type": "reminder_viewed",
                            "client": {"id": tablet_id},
                            "time": time_string,
                            "version": "v1",
                            "data": message_data,
                            }
        return outgoing_message

    async def send_sleep_report(self, tablet_id: str, response: str, question="How did you sleep?"):
        start_time = datetime.utcnow()

        outgoing_message = await self._get_report_defaults(tablet_id)
        outgoing_message["data"]["message"] = question
        outgoing_message["data"]["type"] = "sleep_quality"
        outgoing_message["data"]["response"] = response

        self.save_to_history(channel=CommunicationChannel.LIZZ_API, tablet=tablet_id,
                             message_in="", message_out="report_sleep_quality",
                             start_time=start_time)

        await self._lizz_tablet_ws.send(json.dumps(outgoing_message))

    async def send_meal_report(self, tablet_id: str, response: str, question="Have you had your meal?"):
        start_time = datetime.utcnow()

        outgoing_message = await self._get_report_defaults(tablet_id)
        outgoing_message["data"]["message"] = question
        outgoing_message["data"]["type"] = "meal"
        outgoing_message["data"]["response"] = response

        self.save_to_history(channel=CommunicationChannel.LIZZ_API, tablet=tablet_id,
                             message_in="", message_out="report_meal",
                             start_time=start_time)
        await self._lizz_tablet_ws.send(json.dumps(outgoing_message))

    async def send_medication_report(self, tablet_id: str, response: str, question="Have you had your medication?"):
        start_time = datetime.utcnow()

        outgoing_message = await self._get_report_defaults(tablet_id)
        outgoing_message["data"]["message"] = question
        outgoing_message["data"]["type"] = "medication"
        outgoing_message["data"]["response"] = response

        self.save_to_history(channel=CommunicationChannel.LIZZ_API, tablet=tablet_id,
                             message_in="", message_out="report_medication",
                             start_time=start_time)
        await self._lizz_tablet_ws.send(json.dumps(outgoing_message))

    async def send_mood_report(self, tablet_id: str, response: str, question="How do you feel?"):
        start_time = datetime.utcnow()

        outgoing_message = await self._get_report_defaults(tablet_id)
        outgoing_message["data"]["message"] = question
        outgoing_message["data"]["type"] = "mood"
        outgoing_message["data"]["response"] = response

        self.save_to_history(channel=CommunicationChannel.LIZZ_API, tablet=tablet_id,
                             message_in="", message_out="report_mood",
                             start_time=start_time)
        await self._lizz_tablet_ws.send(json.dumps(outgoing_message))

    async def send_activity_report(self, tablet_id: str, response: str, question="Were you active today?"):
        start_time = datetime.utcnow()

        outgoing_message = await self._get_report_defaults(tablet_id)
        outgoing_message["data"]["message"] = question
        outgoing_message["data"]["type"] = "activity"
        outgoing_message["data"]["response"] = response

        self.save_to_history(channel=CommunicationChannel.LIZZ_API, tablet=tablet_id,
                             message_in="", message_out="report_activity",
                             start_time=start_time)
        await self._lizz_tablet_ws.send(json.dumps(outgoing_message))

    async def show_video(self, tablet_id: str, title: str, url: str):
        start_time = datetime.utcnow()

        message_data = {
            "title": title,
            "url": url
        }
        outgoing_message = {"type": "tablet_show_video",
                            "client": {"id": tablet_id, "type": "TABLET"},
                            "version": "v1",
                            "data": message_data,
                            }
        self.save_to_history(channel=CommunicationChannel.LIZZ_API, tablet=tablet_id,
                             message_in="", message_out="tablet_show_video",
                             start_time=start_time)
        await self._lizz_api_ws.send(json.dumps(outgoing_message))

    async def show_dialogue_screen(self, tablet_id: str):
        start_time = datetime.utcnow()

        message_data = {
            "screenId": "external-interaction",
        }
        outgoing_message = {"type": "tablet_go_to_screen",
                            "client": {"id": tablet_id, "type": "TABLET"},
                            "version": "v1",
                            "data": message_data,
                            }
        self.save_to_history(channel=CommunicationChannel.LIZZ_API, tablet=tablet_id,
                             message_in="", message_out="tablet_show_dialogue",
                             start_time=start_time)
        await self._lizz_api_ws.send(json.dumps(outgoing_message))

    async def show_home_screen(self, tablet_id: str):
        start_time = datetime.utcnow()

        message_data = {
            "screenId": "home",
        }
        outgoing_message = {"type": "tablet_go_to_screen",
                            "client": {"id": tablet_id, "type": "TABLET"},
                            "version": "v1",
                            "data": message_data,
                            }
        self.save_to_history(channel=CommunicationChannel.LIZZ_API, tablet=tablet_id,
                             message_in="", message_out="tablet_show_home",
                             start_time=start_time)
        await self._lizz_api_ws.send(json.dumps(outgoing_message))

    async def _respond(self, msg: dict, channel: CommunicationChannel, delay_before_foreground_action=5):
        start_time = datetime.utcnow()

        """
        Unpack the data
        """
        tablet, user_id, message_type, message_text = "", "", "", ""
        try:
            tablet = msg["client"]["id"]
            user_id = msg["data"]["user"]["id"] if "user" in msg["data"] and "id" in msg["data"]["user"] else ""
            message_type = msg["data"]["responseButton"]["value"]
            message_text = msg["data"]["responseButton"]["label"]
            message_data = {"message": "...",
                            "messageTts": "   ",
                            "message_id": "is-typing",
                            "buttons": [],
                            "extra": json.dumps(emote.get_emotes_from_keys({})),
                            "listen": "manual"}
            outgoing_message = {"type": "external_interaction_message",
                                "data": message_data,
                                "client": msg["client"]}
            self.save_to_history(channel=channel, user=user_id, tablet=tablet,
                                 message_in=message_text, message_out=outgoing_message["data"]["message"],
                                 start_time=start_time)
            await self._lizz_api_ws.send(json.dumps(outgoing_message))  # first queue the message
            await self.show_dialogue_screen(tablet)  # if that was successful, show the dialogue screen

            start_time = datetime.utcnow()

            key = msg["data"]["message_id"]
            if key in ["rich-empathy-conversation", "basic-empathy-conversation"]:
                func = gpt.generate_response
            else:
                func = simple.generate_response
            """
            Determine user's preferred language
            """
            lang = (await self.get_client_data(tablet_id=tablet))["CLIENT-LANG"]

            """
            Generate response message
            """
            outgoing_message, tablet_actions = await func(msg, controller=self, lang=lang)

            delay_before_foreground_action = len(
                outgoing_message["data"]["message"]) * 0.1  # dependent on message length

            foreground_action = False
            for act in tablet_actions:
                if not action.TabletActions(act).is_background_action:
                    foreground_action = True

            if outgoing_message["data"]["message_id"] == "conversation-end":
                outgoing_message["data"]["buttons"] = []
                outgoing_message["data"]["messageTts"] = outgoing_message["data"]["message"]
                outgoing_message["data"]["listen"] = "manual"
                if not foreground_action:
                    if not tablet_actions:
                        tablet_actions = {}
                    tablet_actions[action.TabletActions.screen_action_show_home_screen.value] = "no_arg"
                    foreground_action = True
            else:
                outgoing_message["data"]["listen"] = "after-tts"
                if not outgoing_message["data"]["buttons"]:
                    outgoing_message["data"]["buttons"] = []
                    outgoing_message["data"]["messageTts"] = outgoing_message["data"]["message"]
                else:
                    outgoing_message["data"]["messageTts"] = outgoing_message["data"]["message"]
            if foreground_action:
                if "extra" in outgoing_message["data"]:
                    extra = json.loads(outgoing_message["data"]["extra"])
                else:
                    extra = {}
                extra["hideAfter"] = delay_before_foreground_action
                outgoing_message["data"]["extra"] = json.dumps(extra)

            self.save_to_history(channel=channel, user=user_id, tablet=tablet,
                                 message_in=message_text, message_out=outgoing_message["data"]["message"],
                                 start_time=start_time)

            await self._lizz_api_ws.send(json.dumps(outgoing_message))  # first queue the message
            await self.show_dialogue_screen(tablet)  # if that was successful, show the dialogue screen

            if foreground_action:
                await asyncio.sleep(delay_before_foreground_action + 2)
            await action.queue_tablet_actions(tablet_actions, tablet, self)

        except Exception as e:
            self.save_to_history(channel=channel, user=user_id, tablet=tablet,
                                 message_in=message_text, message_out="error, failed to respond: " + e.__str__(),
                                 start_time=start_time)

    async def _request_tablet_user_data(self, tablet_id: str, user_id=""):
        start_time = datetime.utcnow()

        if not self._lizz_api_ws:
            return {"success": False, "message": "No connection to Liz API"}

        outgoing_message = {"type": "tablet_user_data",
                            "client": {"id": tablet_id}
                            }
        self._data_queue[tablet_id] = {"status": RequestStatus.PENDING, "requested_at": start_time}

        await self._lizz_api_ws.send(json.dumps(outgoing_message))
        print(
            "[" + CommunicationChannel.LIZZ_API + " (OUT)] Fetching client user data for tablet with id: " + tablet_id)
        self.save_to_history(channel=CommunicationChannel.LIZZ_API, user=user_id, tablet=tablet_id, message_in="",
                             message_out="data_request", start_time=start_time)
        return {"success": True}

    async def _request_tablet_calendar_data(self, tablet_id: str, day: datetime, user_id=""):
        start_time = datetime.utcnow()

        if not self._lizz_api_ws:
            return {"success": False, "message": "No connection to Liz API"}

        queue_id = tablet_id + RequestAppend.CALENDAR + day.strftime("%Y-%m-%d")
        outgoing_message = {"type": "tablet_user_calendar",
                            "client": {"id": tablet_id},
                            "data": {"queue_id": queue_id, "day": day.strftime("%Y-%m-%d")}
                            }
        self._data_queue[queue_id] = {"status": RequestStatus.PENDING, "requested_at": start_time}

        await self._lizz_api_ws.send(json.dumps(outgoing_message))
        print(
            "[" + CommunicationChannel.LIZZ_API + " (OUT)] Fetching client calendar data for tablet with id: " + tablet_id)
        self.save_to_history(channel=CommunicationChannel.LIZZ_API, user=user_id, tablet=tablet_id, message_in="",
                             message_out="calendar_request", start_time=start_time)

        return {"success": True, "id": queue_id}

    async def _request_tablet_report_data(self, tablet_id: str, day: datetime, lookback_hours=24, user_id=""):
        start_time = datetime.utcnow()

        if not self._lizz_api_ws:
            return {"success": False, "message": "No connection to Liz API"}

        queue_id = tablet_id + RequestAppend.REPORT + day.strftime("%Y-%m-%d")
        outgoing_message = {"type": "tablet_reports_and_configurations",
                            "client": {"id": tablet_id},
                            "data": {"queue_id": queue_id,
                                     "from": (day - timedelta(hours=lookback_hours)).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                                     "to": day.strftime("%Y-%m-%dT%H:%M:%S.000Z")}
                            }
        self._data_queue[queue_id] = {"status": RequestStatus.PENDING, "requested_at": start_time}

        await self._lizz_api_ws.send(json.dumps(outgoing_message))
        print(
            "[" + CommunicationChannel.LIZZ_API + " (OUT)] Fetching client user data for tablet with id: " + tablet_id)
        self.save_to_history(channel=CommunicationChannel.LIZZ_API, user=user_id, tablet=tablet_id, message_in="",
                             message_out="report_request", start_time=start_time)

        return {"success": True, "id": queue_id}

    async def _request_weather_data(self, tablet_id: str, request_type: WeatherRequest, lang="en", user_id=""):
        start_time = datetime.utcnow()

        if not self._external_api:
            return {"success": False, "message": "No session for external requests."}
        queue_id = tablet_id + RequestAppend.WEATHER + str(request_type)
        if not os.getenv("WEATHER_API_KEY"):
            return {"success": False, "id": queue_id, "message": "No valid API key found"}

        location = await self.get_client_data(tablet_id)
        location = location["CLIENT-LOCATION-CITY"] + ", " + location["CLIENT-LOCATION-COUNTRY"]
        locs = await self.get_geocode_data(location, lang)
        loc = locs[0]

        params = {"lat": loc["lat"], "lon": loc["lon"], "appid": os.getenv("WEATHER_API_KEY"), "lang": lang,
                  "units": "metric"}
        if request_type == WeatherRequest.NOW:
            url = "https://api.openweathermap.org/data/2.5/weather"
        elif request_type == WeatherRequest.FORECAST:
            url = "https://api.openweathermap.org/data/2.5/forecast"
            params["cnt"] = 20  # for now we limit the number of forecasts we receive to approx 48 hours
        else:
            return {"success": False, "id": queue_id, "message": "Invalid weather request type"}

        self._data_queue[queue_id] = {"status": RequestStatus.PENDING, "requested_at": start_time}
        self.save_to_history(channel=CommunicationChannel.EXTERNAL, user=user_id, tablet=tablet_id, message_in="",
                             message_out="weather_request_" + str(request_type), start_time=start_time)
        success = False
        try:
            resp = await self._external_api.get(url, params=params)
            response = await resp.json()
            if "cod" not in response or str(response["cod"]) != "200":
                self._data_queue[queue_id]["status"] = RequestStatus.FAILED
                self._data_queue[queue_id]["data"] = []
            else:
                self._data_queue[queue_id]["status"] = RequestStatus.RECEIVED
                self._data_queue[queue_id]["data"] = response
                success = True

        except Exception as e:
            self._data_queue[queue_id]["status"] = RequestStatus.FAILED
            print(
                "[" + CommunicationChannel.QUART_SERVER + "] Something went wrong with a weather request: " + e.__str__())

        self.save_to_history(channel=CommunicationChannel.EXTERNAL, user=user_id, tablet=tablet_id,
                             message_in="weather_data_" + str(request_type),
                             message_out=self._data_queue[queue_id]["status"], start_time=start_time)
        return {"success": success, "id": queue_id}

    async def _request_news_data(self, tablet_id: str, lang="en", user_id=""):
        start_time = datetime.utcnow()

        if not self._external_api:
            return {"success": False, "message": "No session for external requests."}
        queue_id = tablet_id + RequestAppend.NEWS
        if not os.getenv("NEWS_DATA_KEY"):
            return {"success": False, "id": queue_id, "message": "No valid API key found"}

        location = await self.get_client_data(tablet_id)
        location = location["CLIENT-LOCATION-CITY"] + ", " + location["CLIENT-LOCATION-COUNTRY"]
        locs = await self.get_geocode_data(location, lang)
        loc = locs[0]

        params = {"country": loc["country"].lower(), "apiKey": os.getenv("NEWS_DATA_KEY"), "pageSize": 10}
        url = "https://newsapi.org/v2/top-headlines"

        self._data_queue[queue_id] = {"status": RequestStatus.PENDING, "requested_at": start_time}
        self.save_to_history(channel=CommunicationChannel.EXTERNAL, user=user_id, tablet=tablet_id, message_in="",
                             message_out="news_request", start_time=start_time)
        success = False
        try:
            resp = await self._external_api.get(url, params=params)
            response = await resp.json()
            if "status" not in response or str(response["status"]) != "ok":
                self._data_queue[queue_id]["status"] = RequestStatus.FAILED
                self._data_queue[queue_id]["data"] = []
            else:
                self._data_queue[queue_id]["status"] = RequestStatus.RECEIVED
                self._data_queue[queue_id]["data"] = response
                success = True

        except Exception as e:
            self._data_queue[queue_id]["status"] = RequestStatus.FAILED
            print(
                "[" + CommunicationChannel.QUART_SERVER + "] Something went wrong with a news request: " + e.__str__())

        self.save_to_history(channel=CommunicationChannel.EXTERNAL, user=user_id, tablet=tablet_id,
                             message_in="news_data",
                             message_out=self._data_queue[queue_id]["status"], start_time=start_time)
        return {"success": success, "id": queue_id}

    async def _request_geocode_data(self, location: str, lang="en"):
        start_time = datetime.utcnow()
        if not self._external_api:
            return {"success": False, "message": "No session for external requests."}
        queue_id = RequestPrepend.GEOCODE + location

        if not os.getenv("WEATHER_API_KEY"):
            return {"success": False, "id": queue_id, "message": "No valid API key found"}

        params = {"q": location, "appid": os.getenv("WEATHER_API_KEY"), "lang": lang, "limit": 1}
        url = "http://api.openweathermap.org/geo/1.0/direct"

        self._data_queue[queue_id] = {"status": RequestStatus.PENDING, "requested_at": start_time}
        self.save_to_history(channel=CommunicationChannel.EXTERNAL, user="", tablet="", message_in="",
                             message_out="geocode_request", start_time=start_time)
        success = False
        try:
            resp = await self._external_api.get(url, params=params)
            response = await resp.json()
            self._data_queue[queue_id]["status"] = RequestStatus.RECEIVED
            self._data_queue[queue_id]["data"] = response
            success = True

        except Exception as e:
            self._data_queue[queue_id]["status"] = RequestStatus.FAILED
            print(
                "[" + CommunicationChannel.QUART_SERVER + "] Something went wrong with a geocode request: " + e.__str__())

        self.save_to_history(channel=CommunicationChannel.EXTERNAL, user="", tablet="",
                             message_in="geocode_data",
                             message_out=self._data_queue[queue_id]["status"], start_time=start_time)
        return {"success": success, "id": queue_id}

    async def _handle_conversation_request(self, data: dict):
        if data["type"] == "message_shown":
            return
        elif data["type"] == "message_viewed" or data["type"] == "external_interaction_response":
            return await self._respond(msg=data, channel=CommunicationChannel.LIZZ_API)
        return False

    async def _handle_conversation_end(self, data: dict):
        start_time = datetime.utcnow()
        tablet_id = data["client"]["id"]
        user_id = data["data"]["user"]["id"] if "user" in data["data"] and "id" in data["data"]["user"] else ""

        if data["type"] == "message_shown":
            return True
        elif data["type"] == "message_viewed":
            self.save_to_history(channel=CommunicationChannel.LIZZ_API, user=user_id, tablet=tablet_id,
                                 message_in="conversation-end",
                                 message_out="", start_time=start_time)
            return True
        return False

    async def _handle_data_response(self, data: dict):
        start_time = datetime.utcnow()
        tablet_id = data["client"]["id"]
        if tablet_id not in self._data_queue:
            self._data_queue[tablet_id] = {"status": RequestStatus.PENDING}
            self.save_to_history(channel=CommunicationChannel.LIZZ_API, user="", tablet=tablet_id,
                                 message_in="tablet_user_data",
                                 message_out="[WARNING] Received data for id that was not in queue.",
                                 start_time=start_time)
        self._data_queue[tablet_id]["received_at"] = start_time

        try:
            user_data = None
            self._data_queue[tablet_id]["data"] = {}
            if "user" in data["data"]:
                user_data = data["data"]["user"]
            if not user_data:
                self._data_queue[tablet_id]["status"] = RequestStatus.FAILED

                print(
                    "[" + CommunicationChannel.LIZZ_API + " (IN)] Received empty user data from tablet with id: " + tablet_id)
                self.save_to_history(channel=CommunicationChannel.LIZZ_API, user="", tablet=tablet_id,
                                     message_in="tablet_user_data",
                                     message_out=self._data_queue[tablet_id]["status"], start_time=start_time)
                return False

            if "id" in user_data:
                self._data_queue[tablet_id]["data"]["CLIENT-ID"] = user_data["id"]
            if "name" in user_data:
                self._data_queue[tablet_id]["data"]["CLIENT-NAME"] = user_data["name"]
            if "address" in user_data and user_data["address"]:
                if "," in user_data["address"]:
                    self._data_queue[tablet_id]["data"]["CLIENT-LOCATION-CITY"] = user_data["address"].split(",")[
                        0].strip()
                    self._data_queue[tablet_id]["data"]["CLIENT-LOCATION-COUNTRY"] = user_data["address"].split(",")[
                        1].strip()
                else:  # We assume that if there is no comma, it is only a city
                    self._data_queue[tablet_id]["data"]["CLIENT-LOCATION-CITY"] = user_data["address"].strip()
                    self._data_queue[tablet_id]["data"]["CLIENT-LOCATION-COUNTRY"] = "Nederland"
            else:
                self._data_queue[tablet_id]["data"]["CLIENT-LOCATION-CITY"] = "Nijmegen"
                self._data_queue[tablet_id]["data"]["CLIENT-LOCATION-COUNTRY"] = "Nederland"

            lang_map = {"english": "en", "eng": "en", "en": "en", "dutch": "nl", "nederlands": "nl", "nl": "nl"}
            if "language" in user_data:
                self._data_queue[tablet_id]["data"]["CLIENT-LANG"] = lang_map[user_data["language"].lower()]

            self._data_queue[tablet_id]["status"] = RequestStatus.RECEIVED
            print("[" + CommunicationChannel.LIZZ_API + " (IN)] Received user data from tablet with id: " + tablet_id)
            self.save_to_history(channel=CommunicationChannel.LIZZ_API, user=user_data["id"], tablet=tablet_id,
                                 message_in="tablet_user_data",
                                 message_out=self._data_queue[tablet_id]["status"], start_time=start_time)
        except Exception as e:
            self._data_queue[tablet_id]["status"] = RequestStatus.FAILED

            print(
                "[" + CommunicationChannel.LIZZ_API + " (IN)] Error: " + e.__str__())
            self.save_to_history(channel=CommunicationChannel.LIZZ_API, user="", tablet=tablet_id,
                                 message_in="tablet_user_data",
                                 message_out=e.__str__(), start_time=start_time)
            return False
        return True

    async def _handle_calendar_response(self, data: dict):
        start_time = datetime.utcnow()
        tablet_id = data["client"]["id"]
        day = data["data"]["day"]
        queue_id = tablet_id + RequestAppend.CALENDAR + day
        if queue_id not in self._data_queue:
            self._data_queue[queue_id] = {"status": RequestStatus.PENDING}
            self.save_to_history(channel=CommunicationChannel.LIZZ_API, user="", tablet=tablet_id,
                                 message_in="tablet_calendar_data",
                                 message_out="[WARNING] Received data for id that was not in queue.",
                                 start_time=start_time)
        self._data_queue[queue_id]["received_at"] = start_time

        try:
            calendar_data = []
            user_id = data["data"]["user"]["id"] if "user" in data["data"] and "id" in data["data"]["user"] else ""

            if "calendar" in data["data"]:
                calendar_data = data["data"]["calendar"]
            self._data_queue[queue_id]["data"] = calendar_data
            if not calendar_data:
                self._data_queue[queue_id]["status"] = RequestStatus.FAILED
                print(
                    "[" + CommunicationChannel.LIZZ_API + " (IN)] Received empty calendar data from tablet with id: " + tablet_id)
                self.save_to_history(channel=CommunicationChannel.LIZZ_API, user=user_id, tablet=tablet_id,
                                     message_in="tablet_calendar_data",
                                     message_out=self._data_queue[queue_id]["status"], start_time=start_time)
                return False

            self._data_queue[queue_id]["status"] = RequestStatus.RECEIVED
            print(
                "[" + CommunicationChannel.LIZZ_API + " (IN)] Received calendar data from tablet with id: " + tablet_id)
            self.save_to_history(channel=CommunicationChannel.LIZZ_API, user=user_id, tablet=tablet_id,
                                 message_in="tablet_calendar_data",
                                 message_out=self._data_queue[queue_id]["status"], start_time=start_time)

        except Exception as e:
            self._data_queue[tablet_id]["status"] = RequestStatus.FAILED

            print(
                "[" + CommunicationChannel.LIZZ_API + " (IN)] Error: " + e.__str__())
            self.save_to_history(channel=CommunicationChannel.LIZZ_API, user="", tablet=tablet_id,
                                 message_in="tablet_calendar_data",
                                 message_out=e.__str__(), start_time=start_time)
            return False
        return True

    async def _handle_report_response(self, data: dict):
        start_time = datetime.utcnow()
        tablet_id = data["client"]["id"]
        queue_id = tablet_id + RequestAppend.REPORT + start_time.strftime("%Y-%m-%d")
        if queue_id not in self._data_queue:
            self._data_queue[queue_id] = {"status": RequestStatus.PENDING}
            self.save_to_history(channel=CommunicationChannel.LIZZ_API, user="", tablet=tablet_id,
                                 message_in="tablet_report_data",
                                 message_out="[WARNING] Received data for id that was not in queue.",
                                 start_time=start_time)
        self._data_queue[queue_id]["received_at"] = start_time

        try:
            report_data, configs_time = [], []
            user_id = data["data"]["user"]["id"] if "user" in data["data"] and "id" in data["data"]["user"] else ""

            if "reports" in data["data"]:
                report_data = data["data"]["reports"]
            if "reminderConfigsAndTime" in data["data"]:
                configs_time = data["data"]["reminderConfigsAndTime"]

            self._data_queue[queue_id]["data"] = {"last_24h": report_data, "future": configs_time}

            if not report_data:
                self._data_queue[queue_id]["status"] = RequestStatus.FAILED
                print(
                    "[" + CommunicationChannel.LIZZ_API + " (IN)] Received empty report data from tablet with id: " + tablet_id)
                self.save_to_history(channel=CommunicationChannel.LIZZ_API, user=user_id, tablet=tablet_id,
                                     message_in="tablet_report_data",
                                     message_out=self._data_queue[queue_id]["status"], start_time=start_time)
                return False

            self._data_queue[queue_id]["status"] = RequestStatus.RECEIVED
            print("[" + CommunicationChannel.LIZZ_API + " (IN)] Received report data from tablet with id: " + tablet_id)
            self.save_to_history(channel=CommunicationChannel.LIZZ_API, user=user_id, tablet=tablet_id,
                                 message_in="tablet_report_data",
                                 message_out=self._data_queue[queue_id]["status"], start_time=start_time)

        except Exception as e:
            self._data_queue[tablet_id]["status"] = RequestStatus.FAILED

            print(
                "[" + CommunicationChannel.LIZZ_API + " (IN)] Error: " + e.__str__())
            self.save_to_history(channel=CommunicationChannel.LIZZ_API, user="", tablet=tablet_id,
                                 message_in="tablet_report_data",
                                 message_out=e.__str__(), start_time=start_time)
            return False
        return True

    async def get_client_data(self, tablet_id: str, interval=0.5, refresh_time_mins=60):
        # first check if this data is already known in the session, no need to pull it again unless its time to refresh
        time_since_refresh = datetime.utcnow() - timedelta(minutes=refresh_time_mins)
        if tablet_id not in self._data_queue or self._data_queue[tablet_id]["status"] == RequestStatus.FAILED or \
                self._data_queue[tablet_id]["requested_at"] < time_since_refresh:
            await self._request_tablet_user_data(tablet_id)  # if necessary, send a request
        while self._data_queue[tablet_id]["status"] == RequestStatus.PENDING:
            await asyncio.sleep(interval)  # await the request response

        return copy.deepcopy(self._data_queue[tablet_id]["data"])

    async def get_calendar_data(self, tablet_id: str, day: datetime, interval=0.5, refresh_time_mins=5):
        # first check if this data is already known in the session, no need to pull it again unless its time to refresh
        time_since_refresh = datetime.utcnow() - timedelta(minutes=refresh_time_mins)
        queue_id = tablet_id + RequestAppend.CALENDAR + day.strftime("%Y-%m-%d")

        if queue_id not in self._data_queue or self._data_queue[queue_id]["status"] == RequestStatus.FAILED or \
                self._data_queue[queue_id]["requested_at"] < time_since_refresh:
            await self._request_tablet_calendar_data(tablet_id, day)  # if necessary, send a request

        while self._data_queue[queue_id]["status"] == RequestStatus.PENDING:
            await asyncio.sleep(interval)  # await the request response

        return copy.deepcopy(self._data_queue[queue_id]["data"])

    async def get_report_data(self, tablet_id: str, day: datetime, lookback_hours=24, interval=0.5,
                              refresh_time_mins=1):
        # first check if this data is already known in the session, no need to pull it again unless its time to refresh
        time_since_refresh = datetime.utcnow() - timedelta(minutes=refresh_time_mins)
        queue_id = tablet_id + RequestAppend.REPORT + day.strftime("%Y-%m-%d")

        if queue_id not in self._data_queue or self._data_queue[queue_id]["status"] == RequestStatus.FAILED or \
                self._data_queue[queue_id]["requested_at"] < time_since_refresh:
            await self._request_tablet_report_data(tablet_id, day, lookback_hours)  # if necessary, send a request

        while self._data_queue[queue_id]["status"] == RequestStatus.PENDING:
            await asyncio.sleep(interval)  # await the request response

        return copy.deepcopy(self._data_queue[queue_id]["data"])

    async def get_weather_now_data(self, tablet_id: str, lang="en", interval=0.5, refresh_time_mins=5):
        # first check if this data is already known in the session, no need to pull it again unless its time to refresh
        time_since_refresh = datetime.utcnow() - timedelta(minutes=refresh_time_mins)
        request_type = WeatherRequest.NOW
        queue_id = tablet_id + RequestAppend.WEATHER + str(request_type)
        if queue_id not in self._data_queue or self._data_queue[queue_id]["status"] == RequestStatus.FAILED or \
                self._data_queue[queue_id]["requested_at"] < time_since_refresh:
            await self._request_weather_data(tablet_id, request_type=request_type,
                                             lang=lang)  # if necessary, send a request

        while self._data_queue[queue_id]["status"] == RequestStatus.PENDING:
            await asyncio.sleep(interval)  # await the request response

        return copy.deepcopy(self._data_queue[queue_id]["data"])

    async def get_weather_forecast_data(self, tablet_id: str, lang="en", interval=0.5, refresh_time_mins=0.5):
        # first check if this data is already known in the session, no need to pull it again unless its time to refresh
        time_since_refresh = datetime.utcnow() - timedelta(minutes=refresh_time_mins)
        request_type = WeatherRequest.FORECAST
        queue_id = tablet_id + RequestAppend.WEATHER + str(request_type)
        if queue_id not in self._data_queue or self._data_queue[queue_id]["status"] == RequestStatus.FAILED or \
                self._data_queue[queue_id]["requested_at"] < time_since_refresh:
            await self._request_weather_data(tablet_id, request_type=request_type,
                                             lang=lang)  # if necessary, send a request

        while self._data_queue[queue_id]["status"] == RequestStatus.PENDING:
            await asyncio.sleep(interval)  # await the request response

        return copy.deepcopy(self._data_queue[queue_id]["data"])

    async def get_geocode_data(self, location: str, lang="en", interval=0.5, refresh_time_mins=180):
        # first check if this data is already known in the session, no need to pull it again unless its time to refresh
        time_since_refresh = datetime.utcnow() - timedelta(minutes=refresh_time_mins)
        queue_id = RequestPrepend.GEOCODE + location
        if queue_id not in self._data_queue or self._data_queue[queue_id]["status"] == RequestStatus.FAILED or \
                self._data_queue[queue_id]["requested_at"] < time_since_refresh:
            await self._request_geocode_data(location, lang=lang)  # if necessary, send a request

        while self._data_queue[queue_id]["status"] == RequestStatus.PENDING:
            await asyncio.sleep(interval)  # await the request response

        return copy.deepcopy(self._data_queue[queue_id]["data"])

    async def get_news_data(self, tablet_id: str, lang="en", interval=0.5, refresh_time_mins=5):
        # first check if this data is already known in the session, no need to pull it again unless its time to refresh
        time_since_refresh = datetime.utcnow() - timedelta(minutes=refresh_time_mins)
        queue_id = tablet_id + RequestAppend.NEWS
        if queue_id not in self._data_queue or self._data_queue[queue_id]["status"] == RequestStatus.FAILED or \
                self._data_queue[queue_id]["requested_at"] < time_since_refresh:
            await self._request_news_data(tablet_id, lang=lang)  # if necessary, send a request

        while self._data_queue[queue_id]["status"] == RequestStatus.PENDING:
            await asyncio.sleep(interval)  # await the request response

        return copy.deepcopy(self._data_queue[queue_id]["data"])

    async def complete_with_gpt(self, messages: list):
        start_time = datetime.utcnow()
        print("[" + CommunicationChannel.OPENAI_API + "] Awaiting completion GPT...")

        completion = await self._openai_api.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=messages,
            temperature=0.7
        )
        content = completion.choices[0].message.content
        content = content.strip("```").strip("json")
        self.save_to_history(channel=CommunicationChannel.OPENAI_API, user="", tablet="",
                             message_in="complete_with_gpt",
                             message_out="completed", start_time=start_time)
        data = json.loads(content)
        return data

    async def transcribe_with_whisper(self, audio):
        start_time = datetime.utcnow()
        print("[" + CommunicationChannel.OPENAI_API + "] Awaiting completion Whisper...")

        transcription = await self._openai_api.audio.transcriptions.create(
            model="whisper-1",
            file=audio,
            language="nl",
            prompt="Mwah, Slecht, Prima, Goed, Erg goed, Het gaat wel, Redelijk, Belabberd, Super, Niet zo goed, Het gaat slecht, Geslapen"
        )
        text_in = transcription.text
        self.save_to_history(channel=CommunicationChannel.OPENAI_API, user="", tablet="",
                             message_in="transcribe_with_whisper",
                             message_out="completed", start_time=start_time)
        return text_in

    async def listen_to_audio(self, record_seconds=RECORD_SECONDS):
        await asyncio.sleep(0.5)
        start_time = datetime.utcnow()
        audio = pyaudio.PyAudio()

        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )

        frames = []

        for i in range(0, int(RATE / CHUNK * record_seconds)):
            data = stream.read(CHUNK)
            frames.append(data)

        stream.close()
        audio.terminate()

        waveFile = wave.open(WAVE_OUTPUT_FILENAME, "wb")
        waveFile.setnchannels(CHANNELS)
        waveFile.setsampwidth(audio.get_sample_size(FORMAT))
        waveFile.setframerate(RATE)
        waveFile.writeframes(b''.join(frames))
        waveFile.close()

        audio = open(WAVE_OUTPUT_FILENAME, "rb")

        self.save_to_history(channel=CommunicationChannel.LIZZ_API, user="", tablet="",
                             message_in="listen_to_audio",
                             message_out="completed", start_time=start_time)

        return audio

    async def get_gpt_history(self, tablet_id: str):
        if tablet_id in self._gpt_history:
            return copy.deepcopy(self._gpt_history[tablet_id])
        else:
            return []

    async def save_gpt_history(self, tablet_id: str, role: str, message: str):
        if not tablet_id in self._gpt_history:
            self._gpt_history[tablet_id] = []
        self._gpt_history[tablet_id].append({"role": role, "content": message})
