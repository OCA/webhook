ESCAPE_CHARS = ['"', "\n", "\r", "\t", "\b", "\f"]
REPLACE_CHARS = ['\\"', "\\n", "\\r", "\\t", "\\b", "\\f"]


def get_escaped_value(record, field):
    field_value = getattr(record, str(field), False)

    if field_value and isinstance(field_value, str):
        field_value = field_value.strip()
        for escape_char, replace_char in zip(ESCAPE_CHARS, REPLACE_CHARS):
            field_value = field_value.replace(escape_char, replace_char)
    return field_value
