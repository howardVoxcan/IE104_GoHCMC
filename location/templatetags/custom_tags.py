from django import template

register = template.Library()

@register.filter
def shorten(value, length=50):
    """Cắt ngắn chuỗi"""
    if len(value) > length:
        return value[:length] + "..."
    return value

@register.filter
def to(start, end):
    """Trả về range từ start đến end (bao gồm cả end)"""
    return range(start, end + 1)
