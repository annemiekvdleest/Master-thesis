import glob
import json

file_list = glob.glob("config/emotes/**/*.json", recursive=True)
emote_list = {}

for file in file_list:
    f = open(file)
    text = f.read()
    f.close()
    data = json.loads(text)
    for emote in data:
        target = emote["target"]
        key = emote["key"]
        if target not in emote_list.keys():
            emote_list[target] = {}
        emote_list[target][key] = emote["routine"]


def get_emotes_from_keys(emote_keys: dict):
    emotes = {"rightHand": emote_list["rightHand"]["default"],
              "leftHand": emote_list["leftHand"]["default"],
              "head": emote_list["head"]["default"]
              }
    if not emote_keys:
        return emotes

    if "righthand" in emote_keys:
        emote_keys["rightHand"] = emote_keys.pop("righthand")
    if "lefthand" in emote_keys:
        emote_keys["leftHand"] = emote_keys.pop("lefthand")

    for key_, value in emote_keys.items():
        if key_ in emote_list and value in emote_list[key_]:
            emotes[key_] = emote_list[key_][value]

    return emotes