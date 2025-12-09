def sort_by_d(content_obj):

    if not isinstance(content_obj, list):
        raise TypeError("A função deve receber uma lista.")

    if len(content_obj) <= 1:
        return content_obj

    if isinstance(content_obj[0], dict):
        return sorted(content_obj, key=lambda x: x["D"], reverse=False)

    if isinstance(content_obj[0], list):
        return sorted(content_obj, key=lambda x: x[-1], reverse=False)
