# Handle client http requests

from flask import Flask

app = Flask(__name__, template_folder='.')


# displays the home screen for the app
@app.route('/', methods=['GET'])
def home():
    return 'Hello world!'
