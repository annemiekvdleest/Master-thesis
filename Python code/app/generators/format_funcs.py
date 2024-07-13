def format_capitalize(message_in: str, lang="en"):
    message_out = str(message_in)

    for char in [". "]:
        message_out = char.join(x[0].capitalize()+x[1:] for x in message_out.split(char) if len(x) > 1)
    return message_out


def format_punctualize(message_in: str, lang="en"):
    message_out = str(message_in)

    if message_in[-1] not in ["?", "!", ".", "¿", "¡"]:
        message_out += "."
    return message_out


def format_all(message_in: str, lang="en"):
    message_out = str(message_in)
    message_out = format_capitalize(message_out, lang)
    message_out = format_punctualize(message_out, lang)
    return message_out
