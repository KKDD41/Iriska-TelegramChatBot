import random
import json


class ModelClientSimplified:
    def __init__(self, fp_to_intents: str):
        self.fp_to_intents = fp_to_intents
        self.intents = []

    def set_up(self):
        self.intents = json.loads(open(self.fp_to_intents).read())["intents"]
        for tag_dict in self.intents:
            tag_dict["patterns"] = [set(message.lower().split()) for message in tag_dict["patterns"]]
        print(self.intents)

    def __predict_class(self, sentence: str):
        pattern_sentence = set([word.lower() for word in sentence.split()])
        for class_dict in self.intents:
            for pattern in class_dict["patterns"]:
                if pattern == pattern_sentence:
                    return class_dict["responses"]
        return []

    def get_response(self, sentence: str):
        responses_set = self.__predict_class(sentence)
        if responses_set:
            return random.choice(responses_set)
        else:
            return "Не совсем поняла :(\nМожете, пожалуйста, переформулировать?"
