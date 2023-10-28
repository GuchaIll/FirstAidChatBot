from flask import Flask, render_template, request
from keras.models import load_model
import tensorflow as tf
from wtforms import (Form, TextField, validators, SubmitField, 
DecimalField, IntegerField)

app = Flask(__name__)


class ReusableForm(Form):
  """User entry form for entering specifics for generation"""
  # Starting seed
  emergency = TextField("Hello I'm first aid bot, how can i help you today?", validators=[
                   validators.InputRequired()])
  # Diversity of predictions
  accuracy = DecimalField('Enter diversity:', default=0.8,
                           validators=[validators.InputRequired(),
                                       validators.NumberRange(min=0.5, max=5.0,
                                                              message='Diversity must be between 0.5 and 5.')])
  # Number of words
  words = IntegerField('Enter number of words to generate:',
                       default=50, validators=[validators.InputRequired(),
                                               validators.NumberRange(min=10, max=100, message='Number of words must be between 10 and 100')])
  # Submit button
  submit = SubmitField("Enter")

def load_keras_model():
    """Load in the pre-trained model"""
    global model
    model = load_model('models/transformer.h5')
    # Required for model to work
    global graph
    graph = tf.get_default_graph()


@app.route("/", methods = ['GET', 'POST'])
def home():

  form = ReusableForm(request.form)

  if request.method == 'POST' and form.validate():
    emergency = request.form['emergency']
    accuracy = float(request.form['accuracy'])
    if not emergency.strip():
      return render_template('home.html', response = report_error(graph = graph))
    else:
      return render_template('home.html', response = generate_response(emergency = emergency, accuracy = accuracy, word = 150, graph = graph)
  load_keras_model()
  return render_template('home.html')



if __name__ == "__main__":
  print("Initializing Flask Server and Keras Model")
  load_keras_model()
  app.run(host='0.0.0.0', debug=True)


