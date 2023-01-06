import random
import json
import torch
import os
from nlp_model import NeuralNet
from nlp_utils import bag_of_words, tokenize
from train import train_model


class ModelClient:
    __slots__ = "device", "intents", "words", "classes", "model", "fp_to_model", "fp_to_intents"

    def __init__(self, fp_to_model: str, fp_to_intents: str):
        self.model = None
        self.classes = None
        self.words = None
        self.intents = None
        self.device = None

        self.fp_to_model = fp_to_model
        self.fp_to_intents = fp_to_intents
        if not os.path.exists(fp_to_model):
            print("Model training")
            train_model(fp_to_model, fp_to_intents)
            print("Model saved successfully")

    def set_up(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        data = torch.load(self.fp_to_model)
        self.intents = json.loads(open(self.fp_to_intents).read())

        self.words = data['all_words']
        self.classes = data['tags']

        self.model = NeuralNet(data["input_size"], data["hidden_size"], data["output_size"]).to(self.device)
        self.model.load_state_dict(data["model_state"])
        self.model.eval()

    def __predict_class(self, sentence: str):
        sentence = tokenize(sentence)
        X = bag_of_words(sentence, self.words)
        X = X.reshape(1, X.shape[0])
        X = torch.from_numpy(X).to(self.device)

        output = self.model(X)
        _, predicted = torch.max(output, dim=1)

        tag = self.classes[predicted.item()]
        probs = torch.softmax(output, dim=1)

        return tag, probs[0][predicted.item()]

    def get_response(self, sentence: str):
        tag, prob = self.__predict_class(sentence)
        if prob.item() > 0.75:
            for intent in self.intents['intents']:
                if tag == intent["tag"]:
                    return random.choice(intent['responses'])
        else:
            return "Не совсем поняла :(\nМожете, пожалуйста, переформулировать?"
