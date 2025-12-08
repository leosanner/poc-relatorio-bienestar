def first_char_uppercase(string:str):
    if len(string) == 0:
        return ""
    
    return string[0].upper() + string[1:].lower()
