import json

f = open("config/style.json")
text = f.read()
f.close()
css = json.loads(text)


def apply(opt: dict, styles: dict):
    if "color" not in styles.keys():
        styles["color"] = "pastel-white"
    for key, value in styles.items():
        opt.update(css[key][value])