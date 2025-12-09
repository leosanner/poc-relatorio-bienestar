import spacy


def first_char_uppercase(string: str):
    if len(string) == 0:
        return ""

    return string[0].upper() + string[1:].lower()


# def to_singular(string: str):
#     nlp = spacy.load("pt_core_news_sm")
#     doc = nlp(string)

#     return " ".join([token.lemma_ for token in doc])


# if __name__ == "__main__":
#     print(to_singular("palavras"))
