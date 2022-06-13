from django.template.defaulttags import register


@register.filter
def get_count(dictionary, key):
    return dictionary.get(key, 0)


@register.filter
def get_value(dictionary, key):
    return dictionary.get(key, '')


@register.filter
def none(value):
    return value if value is not None else ''


@register.filter
def to_int(value):
    return int(value)
