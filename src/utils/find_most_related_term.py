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
    tokens_to_compare = [t.lower() for t in tokens_to_compare]
    cleaned = re.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ\s]", "", string).lower()
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if cleaned.startswith("toxinas"):
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        print(cleaned)
    for token in tokens_to_compare:
        if token in cleaned:
            print(token.lower())
            return True

    return False
