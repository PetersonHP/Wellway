# Handle client http requests

import flask
from flask import Flask
import scraper
import sys

app = Flask(__name__)


# displays the home screen for the app
@app.route('/', methods=['GET'])
def home():
    try:
        location = 'Roma'
        meal = 'Dinner'
        nut_rpt = scraper.get_meal_info(location.lower(), meal)

        rendered = flask.render_template(
            'index.html',
            content = nut_rpt.to_html(classes="table table-striped", index=False),
            location = location,
            meal = meal
        )
        return flask.make_response(rendered)
    except Exception as ex:
        print(sys.argv[0] + ": " + str(ex), file=sys.stderr)
        return 'Internal server error occurred. Please contact the site admin.'
