def remove_empty_values(obj):
    """
    Remove empty values from dict and list:
        - ''
        - False
        - None
        - []
        - {}
    """
    if isinstance(obj, dict):
        out = {}
        for key, value in obj.items():
            value = remove_empty_values(value)
            if remove_empty_values(value):
                out[key] = value
        return out
    if isinstance(obj, list):
        return [remove_empty_values(value) for value in obj] or None
    return obj
