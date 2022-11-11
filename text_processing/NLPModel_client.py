import random
import json
import torch
import os
from nlp_model import NeuralNet
from nlp_utils import bag_of_words, tokenize
from train import train_model


class ModelClient:
    RELAPSE_POLL_OPTIONS = []
    DEPRESSION_POLL_OPTIONS = []

    def __init__(self):
        if not os.path.exists("text_processing/nlp_resources_files/data.pth"):
            print("Model training")
            train_model()

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        data = torch.load("text_processing/nlp_resources_files/data.pth")
        self.intents = json.loads(open('text_processing/nlp_resources_files/intents.json').read())

        self.words = data['all_words']
        self.classes = data['tags']

        self.model = NeuralNet(data["input_size"], data["hidden_size"], data["output_size"]).to(self.device)
        self.model.load_state_dict(data["model_state"])
        self.model.eval()

    def set_up(self, fp_depression_criteria: str, fp_relapse_criteria: str):
        with open(fp_relapse_criteria) as fr:
            self.RELAPSE_POLL_OPTIONS = fr.readlines()
        with open(fp_depression_criteria) as fr:
            self.DEPRESSION_POLL_OPTIONS = fr.readlines()

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
            if tag == "relapse test":
                return "relapse test send"
            elif tag == "depression test":
                return "depression test send"
            for intent in self.intents['intents']:
                if tag == intent["tag"]:
                    return random.choice(intent['responses'])
        else:
            return "Не совсем поняла фразу"
