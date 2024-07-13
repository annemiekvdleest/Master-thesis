import datetime
import glob
import json

import pandas as pd

from . import emote
from . import format_funcs
from . import variable

file_list = glob.glob("config/responses/**/*.tsv", recursive=True)
responses_df = pd.concat([pd.read_csv(filename, sep="\t", index_col=None) for filename in file_list], axis=0,
                         ignore_index=True)
responses_df["emotes"] = responses_df["emotes"].fillna("[]").apply(json.loads)

f = open("config/instructions/rich_assistant.txt")
rich_instructions = f.read()
f.close()

f = open("config/instructions/rich_format.txt")
rich_formats = f.read()
f.close()

f = open("config/instructions/rich_task.txt")
rich_task = f.read()
f.close()

f = open("config/instructions/basic_instructions.txt")
basic_instructions = f.read()
f.close()

f = open("config/instructions/basic_format.txt")
basic_format = f.read()
f.close()


async def from_gpt_rich(controller, chat_history: dict):
    options, colors, emotes = {}, {}, {}

    try:
        ct = datetime.datetime.now()
        messages = [{"role": "system", "content": rich_instructions +
                                                  "\n" + rich_task +
                                                  "\n" + rich_formats +
                                                  "\n" + f"Time is {ct}"}]

        messages = messages + chat_history[-10:]  # laatste 10 berichten, gaat dit goed

        if len(chat_history) == 7:
            messages.append({"role": "system",
                             "content": "Bij deze is het gesprek voorbij. Antwoord nog op de vorige reactie van de gebruiker. "
                                        "Sluit het gesprek af zonder verdere vragen te stellen. "
                                        "Vermijd boodschappen die suggereren dat je "
                                        "beschikbaar of te vinden bent voor toekomstige gesprekken of vragen. "
                                        "Benadruk dat de interactie eindigt en er geen "
                                        "verdere contactmogelijkheden zijn. "})

        data = await controller.complete_with_gpt(messages)

        message = data.get("message", "Er gaat iets fout, probeer opnieuw.").strip()
        default_emotes = {"head": "default",
                          "lefthand": "default",
                          "righthand": "default"}
        emotes = data.get("emotes", default_emotes)
        end_indicator = data.get("end", "no")

    except Exception as e:
        print(str(e))
        message = "Het spijt me, er is iets misgegaan. Probeer het opnieuw."
        options = {}
        emotes = {"head": "sad",
                  "lefthand": "default",
                  "righthand": "default"}

    return message, options, emotes, colors, data, end_indicator


async def from_gpt_basic(controller, chat_history: dict):
    options, colors, emotes = {}, {}, {}

    try:
        ct = datetime.datetime.now()
        messages = [{"role": "system", "content": basic_instructions +
                                                  basic_format +
                                                  "\n" + f"Time is {ct}"}]

        messages = messages + chat_history[-10:]  # laatste 10 berichten, gaat dit goed

        data = await controller.complete_with_gpt(messages)

        message = data.get("message", "Er gaat iets fout, probeer opnieuw.").strip()
        default_emotes = {"head": "default",
                          "lefthand": "default",
                          "righthand": "default"}
        emotes = data.get("emotes", default_emotes)


    except Exception as e:
        print(str(e))
        message = "Het spijt me, er is iets misgegaan. Probeer het opnieuw."
        options = {}
        emotes = {"head": "sad",
                  "lefthand": "default",
                  "righthand": "default"}

    return message, options, emotes, colors, data


async def generate_response(message_in, controller, lang="nl"):
    """
    Unpack the data
    """
    tablet_id = message_in["client"]["id"]
    message_type = message_in["data"]["responseButton"]["value"]
    message_text = message_in["data"]["responseButton"]["label"]

    """
    Save gpt history
    """
    await controller.save_gpt_history(tablet_id, "user", message_text)

    chat_history = await controller.get_gpt_history(tablet_id)

    """
    Generate response
    """
    key = message_in["data"]["message_id"]
    end_indicator = "no"
    if key == "basic-empathy-conversation":
        message_content, response_options, emotes, colors, gpt_data = await from_gpt_basic(controller,
                                                                                            chat_history)
    else:
        message_content, response_options, emotes, colors, gpt_data, end_indicator = await from_gpt_rich(controller,
                                                                                                           chat_history)

    """
    You could choose to add 'template' variables and fill them in after, you could use this function for that
    """
    message_content = await variable.fill(message_content, tablet_id, controller, lang=lang)
    message_content = format_funcs.format_all(message_in=message_content, lang=lang)

    """
    From here, your response is molded into the correct JSON format for Lizz to understand
    """
    message_id = "basic-empathy-conversation" if key == "basic-empathy-conversation" else "rich-empathy-conversation"
    message_data = {"message": message_content, "message_id": message_id, "message_lang": lang,
                    "buttons": response_options}

    if message_id == "basic-empathy-conversation" and len(chat_history) >= 3:
        message_data["message_id"] = "conversation-end"
    if message_id == "rich-empathy-conversation" and len(chat_history) >= 7 or end_indicator == "yes":
        message_data["message_id"] = "conversation-end"

    extra = emote.get_emotes_from_keys(emotes)
    message_data["extra"] = json.dumps(extra)
    outgoing_message = {"type": "external_interaction_message",
                        "data": message_data,
                        "client": message_in["client"]}

    """
    Save gpt history
    """
    await controller.save_gpt_history(tablet_id, "assistant", json.dumps(gpt_data))
    actions = {}

    return outgoing_message, actions


"""
The server will call this function when the user wants to start a conversation, 
it will immediately call your generate_response(get_conversation_starter()) function with this as input message
"""


def get_rich_empathy_starter(tablet_id):
    response_button = {"value": "rich-empathy-starter",  # this is what you will receive to respond to
                       "label": "Start het gesprek met alleen de volgende 'message' (gebruik de goede begroeting): 'Goedemorgen/middag/avond, hoe voel je je vandaag?'."}

    message_data = {"message": "this will not be used",  # this is a placeholder
                    "message_id": "rich-empathy-conversation",  # this denotes that we want to receive the response
                    "responseButton": response_button,
                    "message_lang": "nl"}

    outgoing_message = {"type": "message",
                        "client": {"id": tablet_id},
                        "data": message_data}

    return outgoing_message


def get_basic_empathy_starter(tablet_id):
    response_button = {"value": "basic-empathy-starter",  # this is the prompt use to select a response
                       "label": "Start het gesprek met alleen de volgende 'message' (gebruik de goede begroeting): 'Goedemorgen/middag/avond, hoe voel je je vandaag?'."}  # this is a placeholder

    message_data = {"message": "this will not be used",  # this is a placeholder
                    "message_id": "basic-empathy-conversation",  # this denotes that we want to receive the response
                    "responseButton": response_button,
                    "message_lang": "nl"}
    outgoing_message = {"type": "message",
                        "client": {"id": tablet_id},
                        "data": message_data}
    return outgoing_message
