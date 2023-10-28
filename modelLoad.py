# -*- coding: utf-8 -*-
"""Copy of First Aid Bot

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1IcyNLk6gz4hiUVgZYQrtPmuuGYR9Ca_W
"""

import numpy as np
import sys
import tensorflow as tf

from keras.callbacks import TensorBoard
from keras import layers, models, callbacks, losses

import json
import re
import string
import pickle



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



def header(text, color='black', gen_text=None):
  """Create an HTML header"""

  if gen_text:
      raw_html = f'<h1 style="margin-top:16px;color: {color};font-size:54px"><center>' + str(
          text) + '<span style="color: red">' + str(gen_text) + '</center></h1>'
  else:
      raw_html = f'<h1 style="margin-top:12px;color: {color};font-size:54px"><center>' + str(
          text) + '</center></h1>'
  return raw_html


def box(text, gen_text=None):
  """Create an HTML box of text"""

  if gen_text:
      raw_html = '<div style="padding:8px;font-size:28px;margin-top:28px;margin-bottom:14px;">' + str(
          text) + '<span style="color: red">' + str(gen_text) + '</div>'

  else:
      raw_html = '<div style="border-bottom:1px inset black;border-top:1px inset black;padding:8px;font-size: 28px;">' + str(
          text) + '</div>'
  return raw_html

def addContent(old_html, raw_html):
  """Add html content together"""

  old_html += raw_html
  return old_html

def format_sequence(s):
  """Add spaces around punctuation and remove references to images/citations."""

  # Add spaces around punctuation
  s = re.sub(r'(?<=[^\s0-9])(?=[.,;?])', r' ', s)

  # Remove references to figures
  s = re.sub(r'\((\d+)\)', r'', s)

  # Remove double spaces
  s = re.sub(r'\s\s', ' ', s)
  return s


def remove_spaces(s):
  """Remove spaces around punctuation"""

  s = re.sub(r'\s+([.,;?])', r'\1', s)

  return s

class Load_model:
    def __init__(self):
        VOCAB_SIZE = 10000
        MAX_LEN = 80
        EMBEDDING_DIM = 256
        KEY_DIM = 256
        N_HEADS = 2
        FEED_FORWARD_DIM = 256
        VALIDATION_SPLIT = 0.2
        SEED = 42
        LOAD_MODEL = False
        BATCH_SIZE = 32
        EPOCHS = 5

        inputs = layers.Input(shape=(None,), dtype=tf.int32)
        x = TokenAndPositionEmbedding(MAX_LEN, VOCAB_SIZE, EMBEDDING_DIM)(inputs)
        x, attention_scores = TransformerBlock(N_HEADS, KEY_DIM, EMBEDDING_DIM, FEED_FORWARD_DIM)(x)
        outputs = layers.Dense(VOCAB_SIZE, activation="softmax")(x)
        self.gpt = models.Model(inputs=inputs, outputs=[outputs, attention_scores])
        self.gpt.compile("adam", loss=[lossets.SparseCategoricalCrossenropy(), None])
        self.gpt.summary()


        # Load the model and vocabulary (corrected file paths)
        if LOAD_MODEL:
            self.gpt = models.load_model("models/transformer.h5", compile=True)
            with open("models/vocab.pkl", 'rb') as file:
                self.vocab_saved = pickle.load(file)

        # Create the text generator
        self.text_generator = TextGenerator(self.vocab_saved)
        self.text_generator.model = self.gpt

    def generate_response(self, emergency, accuracy, word):
        gen = self.text_generator.generate("FirstAid: " + emergency, accuracy, word)
        # Corrected variable name from 'start' to 'gen'
        gen = remove_spaces(' '.join(gen))  # Remove spaces around punctuation
        html = ''
        html = addContent(html, header(
            'Input Seed ', color='black', gen_text='Network Output'))
        html = addContent(html, box(emergency, gen))
        return f'<div>{html}'

    # Add 'self' parameter to report_error method
    def report_error(self):
        return f'<div>{'Error: Invalid Entry, Please input the correct instructions'}</div>'