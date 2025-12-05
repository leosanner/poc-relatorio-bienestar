from pathlib import Path
import json
import re

def find_related_term(string:str, tokens_to_compare:list[str]):
    cleaned = re.sub(r'[^\w\s]|_', '', string).lower()

    for token in tokens_to_compare:
        if token.lower() in cleaned:
            return True
        
    return False
