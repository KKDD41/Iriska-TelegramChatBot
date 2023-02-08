import numpy as np
import nltk

nltk.download('punkt')

from nltk import word_tokenize
from nltk.stem.snowball import SnowballStemmer

stemmer = SnowballStemmer("english")
ignore_words = ['?', '.', '!', ',', '/', ')', ':', '(']


def tokenize(sentence):
    return word_tokenize(sentence)


def stem(word):
    return stemmer.stem(word.lower())


def bag_of_words(raw_sentence, words):
    sentence_words = [stem(word) for word in raw_sentence if word not in ignore_words]
    bag = np.zeros(len(words), dtype=np.float32)
    for idx, w in enumerate(words):
        if w in sentence_words:
            bag[idx] = 1
    return bag
