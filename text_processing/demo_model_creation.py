import json
import pickle
import random
import numpy as np
import os
from keras.layers import Dense, Dropout
from keras.optimizers import SGD
import ru_core_news_md
from keras.models import Sequential

nlp = ru_core_news_md.load()

invalid = ["!", "?", ",", ".", "-", "_"]

words = set()
classes = []
documents = []


def clean_up_sentence(sentence: str):
    init_sentence = nlp(sentence)
    return [token.lemma_ for token in init_sentence if token.lemma_ not in invalid]


def preprocessing():
    intents = json.loads(open("C:\\Users\\Kate\\Desktop\\IRISKA\\Irirska-TelegramChatBot\\text_processing\\test_data.json").read())

    for intent in intents["intents"]:
        for pattern in intent["patterns"]:
            message_tokens = clean_up_sentence(pattern)
            for word in message_tokens:
                words.add(word)
            documents.append((message_tokens, intent["tag"]))
            if intent["tag"] not in classes:
                classes.append(intent["tag"])


def create_bag_of_words():
    training = []
    output_empty = [0] * len(words)

    words_lemmas = sorted(words)
    pickle.dump(words_lemmas, open("words.pkl", "wb"))
    pickle.dump(classes, open("classes.pkl", "wb"))

    for doc in documents:
        bag = []
        for word in words_lemmas:
            if word in doc[0]:
                bag.append(1)
            else:
                bag.append(0)

        output_row = output_empty.copy()
        output_row[classes.index(doc[1])] = 1
        training.append([bag, output_row])

    for l in training:
        print(l)
    return training


def create_model():
    preprocessing()
    training = create_bag_of_words()

    random.shuffle(training)
    training = np.array(training)

    train_x = list(training[:, 0])
    train_y = list(training[:, 1])

    model = Sequential()
    model.add(Dense(128, input_shape=(len(train_x[0]),), activation="relu"))
    model.add(Dropout(0.5))
    model.add(Dense(64))
    model.add(Dropout(0.5))
    model.add(Dense(len(train_y[0]), activation="softmax"))

    sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
    model.compile(loss="categorical_crossentropy", optimizer=sgd, metrics=["accuracy"])
    hist = model.fit(np.array(train_x), np.array(train_y), epochs=200, batch_size=5, verbose=1)
    model.save("model_prototype.h5", hist)
    print("Done")


if __name__ == "__main__":
    try:
        os.remove("words.pkl")
        os.remove("classes.pkl")
        os.remove("model_prototype.h5")
    except Exception as error:
        pass
    finally:
        create_model()