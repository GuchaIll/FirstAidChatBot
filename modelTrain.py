# -*- coding: utf-8 -*-
"""First Aid Bot Trained in Google Colab

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1IcyNLk6gz4hiUVgZYQrtPmuuGYR9Ca_W
"""

!pip install -q -U tensorboard-plugin-profile
!pip install opendatasets
!pip install keras
!pip install keras_preprocessing
!pip install tensorflow
!pip install PyPDF2

import numpy as np
import sys
import tensorflow as tf

from keras.callbacks import TensorBoard
from keras import layers, models, callbacks, losses


import json
import re
import string
import matplotlib.pyplot as plt


import opendatasets as od

import os
from google.colab import drive

# Mount Google Drive
drive.mount('/content/drive')

# Create a folder in the root directory
#!mkdir -p "/content/drive/My Drive/FirstAidChatbot"

# importing required modules
from PyPDF2 import PdfReader

# creating a pdf reader object
reader = PdfReader('/content/drive/MyDrive/FirstAidChatbot/RTE_Textbook_Sample.pdf')

# printing number of pages in pdf file
print(len(reader.pages))

# Initialize an empty list to store paragraphs
paragraphs = []

# Loop through each page in the PDF
for page_num in range(14, len(reader.pages)):
    page = reader.pages[page_num]
    page_text = page.extract_text()
    page_text = page_text.replace('\xa0', ' ')
    page_text = page_text.replace('\n', ' ')
    page_text = page_text.replace('____', '')
    pattern = r"Responding to Emergencies  \|   \d+   \|  "
    pattern2 = r"Responding to Emergencies  \|   \d{1,3}    \|  "
    cleaned_text = re.sub(pattern, "", page_text)
    cleaned_text = re.sub(pattern2, "", cleaned_text)
    # Split the page text into paragraphs using regular expressions
    page_paragraphs = re.split(r'\n{2,}', cleaned_text.strip())
    prefix = "Emergency"
    page_paragraphs = [prefix + " " + paragraph for paragraph in page_paragraphs]

    paragraphs.extend(page_paragraphs)

# Convert the list to a NumPy array
paragraphs_array = paragraphs
print(len(paragraphs_array))
# Close the PDF file

#reader = PdfReader('/content/drive/MyDrive/FirstAidChatbot/Hazadous Situation.pdf')

# printing number of pages in pdf file
#print(len(reader.pages))

# Initialize an empty list to store paragraphs
#paragraphs2 = []

# Loop through each page in the PDF
#for page_num in range(156, 372):
   # page = reader.pages[page_num]
   # page_text = page.extract_text()
   # page_text = page_text.replace('\xa0', ' ')
   # page_text = page_text.replace('\n', ' ')
  #  page_text = page_text.replace('____', '')
   # page_text = page_text.replace('•', '')
   # pattern = r"Page \d{1,3} ERG \d{1,4}GUIDE \d{1,3} "
  #  pattern2 = r"Page \d{1,3}"
 #   pattern3 = r"ERG 2020GUIDE \d{1,3}"
 #   pattern4 = r"POTENTIAL HAZARDS"
  #  cleaned_text = re.sub(pattern, "", page_text)
   # cleaned_text = re.sub(pattern2, "", cleaned_text)
   # cleaned_text = re.sub(pattern3, "", cleaned_text)
    #cleaned_text = re.sub(pattern4, "", cleaned_text)
  #  # Split the page text into paragraphs using regular expressions
   # page_paragraphs = re.split(r'\n{2,}', cleaned_text.strip())
 #   prefix = "Emergency"
 #   page_paragraphs = [prefix + " " + paragraph for paragraph in page_paragraphs]

  #  paragraphs2.extend(page_paragraphs)

# Convert the list to a NumPy array
#paragraphs_array2 = paragraphs2[3:]
#print(len(paragraphs2))
# Close the PDF file



od.download("https://www.kaggle.com/datasets/therealsampat/intents-for-first-aid-recommendations/data")

with open('/content/intents-for-first-aid-recommendations/intents.json') as json_data:
  recipe_data = json.load(json_data)

for x in recipe_data['intents']:

  print(x['tag'])
  print(x['patterns'])
  print(x['responses'])

filtered_data = [
    "Emergency" + "Treatment for " + x["tag"] + ' : '  + ' '.join(x["responses"]).lower()
    for x in recipe_data['intents']
    if "tag" in x
    and x['tag'] is not None
    and "patterns" in x
    and x['patterns'] is not None
    and "responses" in x
    and x['responses'] is not None
    and  x['responses'][0].strip()
]
print(filtered_data)
# Count the entries
n_entries = len(filtered_data)
print(f"{n_entries} entries loaded")

example = filtered_data
print(example)

filtered_data = []
count = 0
for x in recipe_data['intents']:
  if ("tag" in x
    and x['tag'] is not None
    and "patterns" in x
    and x['patterns'] is not None
    and "responses" in x
    and x['responses'] is not None
    and  x['responses'][0].strip()):
      for y in range(len(x["patterns"])):
        print( x['patterns'][y])
        element =  "FirstAid:" + x['patterns'][y] + ' '.join(x["responses"]).lower()
        filtered_data.append(element)
        count += 1

filtered_data = filtered_data
print(len(filtered_data))
print(count)
def count_words(s):
    words = s.split()
    return len(words)

max_length = max(filtered_data, key=count_words)
print(max_length)
words = max_length.split()
print(len(words))

text = ' '.join(filtered_data)

# Tokenize the string into words (split by spaces)
words = text.split()

# Create a set to store unique words
unique_words = set(words)

# Calculate the total number of unique words
total_unique_words = len(unique_words)

print("Total number of unique words:", total_unique_words)

VOCAB_SIZE = 3000
MAX_LEN = 150
EMBEDDING_DIM = 256
KEY_DIM = 256
N_HEADS = 2
FEED_FORWARD_DIM = 256
VALIDATION_SPLIT = 0.2
SEED = 42
LOAD_MODEL = False
BATCH_SIZE = 4
EPOCHS = 20

def pad_punctuation(s): #Pad the punctuations, treating them as separarte words
  s = re.sub(f"([{string.punctuation}])", r' \1', s)
  s = re.sub(' +', ' ', s)
  return s

#convert to tensorflow dataset
text_data = [pad_punctuation(x) for x in filtered_data]
text_ds = tf.data.Dataset.from_tensor_slices(text_data).batch(BATCH_SIZE).shuffle(1000)

# Display an example
example_data = text_data[9]
print(example_data)

#Create vectorisation layer
vectorize_layer = layers.TextVectorization(
    standardize = 'lower',
    max_tokens = VOCAB_SIZE,
    output_mode = "int",
    output_sequence_length = MAX_LEN +1,

)


#adapt layer to training set
vectorize_layer.adapt(text_ds)
vocab = vectorize_layer.get_vocabulary()

# Display some token:word mappings
for i, word in enumerate(vocab[:10]):
    print(f"{i}: {word}")

    # Display the same example converted to ints
example_tokenised = vectorize_layer(example_data)
print(example_tokenised.numpy())

#Display same token::word mapping
example_tokenised = vectorize_layer(example_data)
print(example_tokenised.numpy())

def prepare_inputs(text): #create training set of reciped and corresponding y with same text shifted by one word
  text = tf.expand_dims(text,-1)
  tokenized_sentences = vectorize_layer(text)
  x = tokenized_sentences[:,:-1]
  y = tokenized_sentences[:,1:]
  return x,y

train_ds = text_ds.map(prepare_inputs)

example_input_output = train_ds.take(1).get_single_element()
example_input_output[0][0]
example_input_output[1][0]

def causal_attention_mask(batch_size, n_dest, n_src, dtype):
    i = tf.range(n_dest)[:, None]
    j = tf.range(n_src)
    m = i >= j - n_src + n_dest
    mask = tf.cast(m, dtype)
    mask = tf.reshape(mask, [1, n_dest, n_src])
    mult = tf.concat(
        [tf.expand_dims(batch_size, -1), tf.constant([1, 1], dtype=tf.int32)], 0
    )
    return tf.tile(mask, mult)


np.transpose(causal_attention_mask(1, 10, 10, dtype=tf.int32)[0])

class TransformerBlock(layers.Layer):
    def __init__(self, num_heads, key_dim, embed_dim, ff_dim, dropout_rate=0.1):
        super(TransformerBlock, self).__init__()
        self.num_heads = num_heads
        self.key_dim = key_dim
        self.embed_dim = embed_dim
        self.ff_dim = ff_dim
        self.dropout_rate = dropout_rate
        self.attn = layers.MultiHeadAttention(
            num_heads, key_dim, output_shape=embed_dim
        )
        self.dropout_1 = layers.Dropout(self.dropout_rate)
        self.ln_1 = layers.LayerNormalization(epsilon=1e-6)
        self.ffn_1 = layers.Dense(self.ff_dim, activation="relu")
        self.ffn_2 = layers.Dense(self.embed_dim)
        self.dropout_2 = layers.Dropout(self.dropout_rate)
        self.ln_2 = layers.LayerNormalization(epsilon=1e-6)

    def call(self, inputs):
        input_shape = tf.shape(inputs)
        batch_size = input_shape[0]
        seq_len = input_shape[1]
        causal_mask = causal_attention_mask(
            batch_size, seq_len, seq_len, tf.bool
        )
        attention_output, attention_scores = self.attn(
            inputs,
            inputs,
            attention_mask=causal_mask,
            return_attention_scores=True,
        )
        attention_output = self.dropout_1(attention_output)
        out1 = self.ln_1(inputs + attention_output)
        ffn_1 = self.ffn_1(out1)
        ffn_2 = self.ffn_2(ffn_1)
        ffn_output = self.dropout_2(ffn_2)
        return (self.ln_2(out1 + ffn_output), attention_scores)

    def get_config(self):
        config = super().get_config()
        config.update(
            {
                "key_dim": self.key_dim,
                "embed_dim": self.embed_dim,
                "num_heads": self.num_heads,
                "ff_dim": self.ff_dim,
                "dropout_rate": self.dropout_rate,
            }
        )
        return config

class TokenAndPositionEmbedding(layers.Layer):
    def __init__(self, max_len, vocab_size, embed_dim):
        super(TokenAndPositionEmbedding, self).__init__()
        self.max_len = max_len
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.token_emb = layers.Embedding(
            input_dim=vocab_size, output_dim=embed_dim
        )
        self.pos_emb = layers.Embedding(input_dim=max_len, output_dim=embed_dim)

    def call(self, x):
        maxlen = tf.shape(x)[-1]
        positions = tf.range(start=0, limit=maxlen, delta=1)
        positions = self.pos_emb(positions)
        x = self.token_emb(x)
        return x + positions

    def get_config(self):
        config = super().get_config()
        config.update(
            {
                "max_len": self.max_len,
                "vocab_size": self.vocab_size,
                "embed_dim": self.embed_dim,
            }
        )
        return config

inputs = layers.Input(shape=(None,), dtype=tf.int32)
x = TokenAndPositionEmbedding(MAX_LEN, VOCAB_SIZE, EMBEDDING_DIM)(inputs)
x, attention_scores = TransformerBlock(
    N_HEADS, KEY_DIM, EMBEDDING_DIM, FEED_FORWARD_DIM
)(x)
outputs = layers.Dense(VOCAB_SIZE, activation="softmax")(x)
gpt = models.Model(inputs=inputs, outputs=[outputs, attention_scores])
gpt.compile("adam", loss=[losses.SparseCategoricalCrossentropy(), None])
gpt.summary()

if LOAD_MODEL:
  gpt = models.load_model("/content/drive/MyDrive/FirstAidChatbot/models/gpt2", compile = True)



# Create a TextGenerator checkpoint
class TextGenerator(callbacks.Callback):
    def __init__(self, index_to_word, top_k=10):
        self.index_to_word = index_to_word
        self.word_to_index = {
            word: index for index, word in enumerate(index_to_word)
        }

    def sample_from(self, probs, temperature):
        probs = probs ** (1 / temperature)
        probs = probs / np.sum(probs)
        return np.random.choice(len(probs), p=probs), probs

    def generate(self, start_prompt, max_tokens, temperature):
        start_tokens = [
            self.word_to_index.get(x, 1) for x in start_prompt.split()
        ]
        sample_token = None
        info = []
        while len(start_tokens) < max_tokens and sample_token != 0:
            x = np.array([start_tokens])
            y, att = self.model.predict(x, verbose=0)
            sample_token, probs = self.sample_from(y[0][-1], temperature)
            info.append(
                {
                    "prompt": start_prompt,
                    "word_probs": probs,
                    "atts": att[0, :, -1, :],
                }
            )
            start_tokens.append(sample_token)
            if 0 <= sample_token < len(self.index_to_word):
              start_prompt = start_prompt + " " + self.index_to_word[sample_token]
        print(f"\ngenerated text:\n{start_prompt}\n")
        return info

    def on_epoch_end(self, epoch, logs=None):
        self.generate("FirstAid:", max_tokens=150, temperature=0.5)

model_checkpoint_callback = callbacks.ModelCheckpoint(
    filepath = "/content/drive/MyDrive/FirstAidChatbot/checkpoint2/checkpoint2.ckpt",
    save_weights_only = True,
    save_freq = "epoch",
    verbose = 0,
)

tensorboard_callback = callbacks.TensorBoard(log_dir= "/content/drive/MyDrive/FirstAidChatbot/gpt/logs")

text_generator = TextGenerator(vocab)

gpt.fit(train_ds, epochs = EPOCHS, callbacks = [model_checkpoint_callback, tensorboard_callback, text_generator],)

gpt.save("/content/drive/MyDrive/FirstAidChatbot/models/gpt2/transformer.h5")

def print_probs(info, vocab, top_k=5):
    for i in info:
        highlighted_text = []
        for word, att_score in zip(
            i["prompt"].split(), np.mean(i["atts"], axis=0)
        ):
            highlighted_text.append(
                '<span style="background-color:rgba(135,206,250,'
                + str(att_score / max(np.mean(i["atts"], axis=0)))
                + ');">'
                + word
                + "</span>"
            )
        highlighted_text = " ".join(highlighted_text)
        display(HTML(highlighted_text))

        word_probs = i["word_probs"]
        p_sorted = np.sort(word_probs)[::-1][:top_k]
        i_sorted = np.argsort(word_probs)[::-1][:top_k]
        for p, i in zip(p_sorted, i_sorted):
            print(f"{vocab[i]}:   \t{np.round(100*p,2)}%")
        print("--------\n")

info = text_generator.generate(
    "FirstAid: what to do for snake bite ", max_tokens=150, temperature= 0.2
)

print_probs(info, vocab)

info = text_generator.generate(
    "recipe for chocolate ice cream |", max_tokens=7, temperature=1.0
)
print_probs(info, vocab)

# Commented out IPython magic to ensure Python compatibility.
# %load_ext tensorboard
!rm -rf "/content/drive/MyDrive/FirstAidChatbot/lstm/logs"

# Commented out IPython magic to ensure Python compatibility.
# %tensorboard --logdir logs/fit

# Commented out IPython magic to ensure Python compatibility.
# %cp -av "./models" "/content/drive/MyDrive/AnimeGAN/models"
# %cp -av "./checkpoint" "/content/drive/MyDrive/AnimeGAN/checkpoints"