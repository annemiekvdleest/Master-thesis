import pandas as pd
import glob
import numpy as np
import json
from . import format_funcs
from . import variable
from . import emote
from . import style

file_list = glob.glob("config/responses/**/*.tsv", recursive=True)
responses_df = pd.concat([pd.read_csv(filename, sep="\t", index_col=None) for filename in file_list], axis=0,
                         ignore_index=True)
responses_df["emotes"] = responses_df["emotes"].fillna("[]").apply(json.loads)
responses_df["styles"] = responses_df["styles"].fillna("{}").apply(json.loads)
responses_df["lang"] = responses_df["lang"].str.strip()
responses_df["message_content"] = responses_df["message_content"].str.strip()

file_list = glob.glob("config/flows/**/*.tsv", recursive=True)
dialogue_df = pd.concat([pd.read_csv(filename, sep="\t", index_col=None) for filename in file_list], axis=0,
                        ignore_index=True)
dialogue_df = dialogue_df.fillna("")
dialogue_df["user_message_type"] = dialogue_df["user_message_type"].str.strip()
dialogue_df["assistant_output_type"] = dialogue_df["assistant_output_type"].str.strip()

message2responseKey = dict(zip(dialogue_df["user_message_type"], dialogue_df["assistant_output_type"]))
message2options = dict(zip(dialogue_df["user_message_type"], dialogue_df["response_options"]))
message2options = {k: json.loads(v) for k, v in message2options.items() if
                   v is not np.nan and v != ""}  # Remove empty values, load json

message2actions = dict(zip(dialogue_df["user_message_type"], dialogue_df["tablet_actions"]))
message2actions = {k: json.loads(v) for k, v in message2actions.items() if
                   v is not np.nan and v != ""}  # Remove empty values, load json


async def from_key(args: dict, lang: str):
    if "key" not in args:
        return None, None, None
    key = args["key"]

    available_responses = responses_df[responses_df["message_type"] == key]
    responses_lang = available_responses[available_responses["lang"] == lang]

    if len(responses_lang) == 0:
        return None, None, None
    generated_response = responses_lang.sample(1)
    message = generated_response["message_content"].to_numpy()[0]
    emotes = generated_response["emotes"].to_numpy()[0]
    styles = generated_response["styles"].to_numpy()[0]
    return message, emotes, styles


async def generate_response(message_in, controller, lang="nl"):
    """
    Unpack the data
    """
    tablet_id = message_in["client"]["id"]
    message_type = message_in["data"]["responseButton"]["value"]
    message_text = message_in["data"]["responseButton"]["label"]
    response_type = message2responseKey[message_type]

    """
    Generate response
    """
    args = {"message_in": message_in, "key": response_type, "lang": lang}
    message_content, emotes, styles = await from_key(args, lang=lang)
    message_data = {}
    if message_content:
        message_content = await variable.fill(message_content, tablet_id, controller, lang=lang)
        message_content = format_funcs.format_all(message_in=message_content, lang=lang)
        message_data = {"message": message_content,
                        "message_id": "conversation",
                        "message_type": response_type,
                        "message_lang": lang}
        response_options = await get_user_options(message_type, tablet_id, controller, lang=lang)

        if response_options:
            message_data["buttons"] = response_options
        else:
            message_data["buttons"] = {}

        if message_in["data"]["responseButton"]["label"] == "microphone_button":
            message_data["message_id"] = "conversation-end"  # we change the message_id to stop answering Lizz

    else:
        args = {"message_in": message_in, "key": "sorry-no-answer"}
        message_content, emotes, styles = await from_key(args, lang=lang)
        message_content = await variable.fill(message_content, tablet_id, controller, lang=lang)
        message_content = format_funcs.format_all(message_in=message_content, lang=lang)
        message_data = {"message": message_content,
                        "message_id": "conversation-end",  # we change the message_id to stop answering Lizz
                        "message_type": response_type,
                        "message_lang": lang}

    extra = emote.get_emotes_from_keys(emotes)
    message_data["extra"] = json.dumps(extra)
    outgoing_message = {"type": "external_interaction_message",
                        "data": message_data,
                        "client": message_in["client"]}

    return outgoing_message, get_tablet_actions(message_type)


def get_tablet_actions(key: str):
    if key not in message2actions or not message2actions[key]:
        return []
    else:
        return message2actions[key]


async def get_user_options(key: str, tablet_id: str, controller, lang: str):
    if key not in message2options or not message2options[key]:
        return None

    response_options = []
    for option in message2options[key]:
        args = {"key": option}
        msg, _, styles = await from_key(args, lang=lang)
        if msg:  # If we do not have a displayable string, do not present this option
            msg = await variable.fill(message_in=msg, tablet_id=tablet_id, controller=controller, lang=lang)
            msg = format_funcs.format_all(message_in=msg, lang=lang)
            opt = {"value": option, "label": msg, "hexColorText": "#FFFFFF"}
            style.apply(opt, styles)
            response_options.append(opt)

    if not response_options:
        return None

    return response_options


def get_non_empathic_starter(tablet_id):
    response_button = {"value": "non-empathic-starter",  # this is the prompt use to select a response
                       "label": "non-empathic-starter"}  # this is a placeholder

    message_data = {"message": "this will not be used",  # this is a placeholder
                    "message_id": "conversation",  # this denotes that we want to receive the response
                    "responseButton": response_button,
                    "message_lang": "en"}
    outgoing_message = {"type": "external_interaction_message",
                        "client": {"id": tablet_id},
                        "data": message_data}
    return outgoing_message
