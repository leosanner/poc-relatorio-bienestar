import re
from rapidfuzz import fuzz


# def find_related_term(string: str, tokens_to_compare: list[str], threshold=70):
#     print(string)
#     cleaned = re.sub(r"[^\w\s]", " ", string).lower()
#     words = cleaned.split()
#     print(words)
#     print()

#     for token in tokens_to_compare:
#         token = token.lower()
#         for word in words:
#             if fuzz.ratio(token, word) >= threshold:
#                 return True

#     return False


def find_related_term(string: str, tokens_to_compare: list[str]):
    cleaned = re.sub(r"[^\w\s]|_", "", string).lower()
    for token in tokens_to_compare:
        if token.lower() in cleaned:
            return True

    return False
