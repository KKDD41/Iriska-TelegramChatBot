from keras.models import load_model
import json
import pickle
import random
import numpy as np
import os
from demo_model_creation import create_model, clean_up_sentence


class ModelLoader:

    def __init__(self):
        if not os.path.exists("model_prototype.h5"):
            create_model()
        self.words = pickle.load(open("words.pkl", "rb"))
        self.classes = pickle.load(open("classes.pkl", "rb"))
        self.intents = json.loads(open("C:\\Users\\Kate\\Desktop\\IRISKA\\Irirska-TelegramChatBot\\text_processing"
                                       "\\test_data.json").read())
        self.model = load_model("model_prototype.h5")

    def __bag_of_words(self, sentence: str):
        temp_words = clean_up_sentence(sentence)
        bag = [0] * len(self.words)
        for w in temp_words:
            for i, word in enumerate(self.words):
                if w == word:
                    bag[i] = 1
        return np.array(bag)

    def __predict_class(self, sentence: str):
        bow = self.__bag_of_words(sentence)
        res = self.model.predict(np.array([bow]))[0]

        result = [[i, r] for i, r in enumerate(res) if r > 0.25]
        result.sort(key=lambda x: x[1], reverse=True)
        res_list = []
        for r in result:
            res_list.append({"intent": self.classes[r[0]], "probability": str(r[1])})

        return res_list

    def get_response(self, sentence):
        intent_list = self.__predict_class(sentence)
        tag = intent_list[0]["intent"]
        list_of_intents = self.intents["intents"]

        print(intent_list)
        print(list_of_intents)
        for i in list_of_intents:
            if i["tag"] == tag:
                return random.choice(i["response"])

# while True:
#     message = input("")
#     inst = predict_class(message)
#     print(inst)
#     res = get_response(inst, intents)
#     print(res)
