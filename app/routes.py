'''
Handle client http requests
'''

import datetime
import sys

import scraper
from common import DHALL_ARGS

import flask
from flask import Flask


app = Flask(__name__)


def scrape_nutrition():
    '''
    scrape all dining hall nutrition info for the current day and store 
    it in the db
    '''


@app.route('/', methods=['GET'])
def home():
    '''
    displays the home screen for the app
    '''
    return flask.make_response(flask.render_template('index.html'))


@app.route('/getReport', methods=['POST'])
def get_report():
    '''
    displays the nutrition report for the requested meal
    '''
    try:
        location = flask.request.form.get('location')
        meal = flask.request.form.get('meal')
        todays_date = datetime.date.today()

        nut_rpt = scraper.get_meal_info(location, meal, todays_date)

        rendered = flask.render_template(
            'report.html',
            content=nut_rpt.to_html(
                classes="table table-striped", index=False),
            location=DHALL_ARGS[location][1],
            meal=meal
        )
        return flask.make_response(rendered)
    except Exception as ex:
        print(sys.argv[0] + ": " + str(ex), file=sys.stderr)
        return 'Internal server error occurred. Please contact the site admin.'
