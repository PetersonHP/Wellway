'''
Handle client http requests
'''

import atexit
from datetime import datetime
import logging
import os
import sys
import uuid

from common import DINING_HALLS, DHALL_ARGS, MEALS
import database
import scraper

from apscheduler.schedulers.background import BackgroundScheduler
import flask
from flask import Flask


app = Flask(__name__)

log = logging.getLogger(__name__)
logging.basicConfig(filename=f'{os.path.dirname(os.path.abspath(__file__))}' + \
                    f'/logs/wellway-{uuid.uuid1()}.log', level=logging.INFO)


def scrape_nutrition_daily():
    '''
    Scrape all dining hall nutrition info for the current day and store 
    it in the db

    It may be better to parallelize this in the future
    '''
    log.info('Scraping nutrition info at %s' % datetime.today())

    todays_date = datetime.today()
    for hall in DINING_HALLS:
        for meal in MEALS:
            report = scraper.get_meal_info(hall, meal, todays_date)
            if report.empty:
                log.debug('No data available for %s %s' % (hall, meal))
            else:
                log.debug('Storing %s %s' % (hall, meal))
                database.store_nut_rpt(hall, meal, todays_date, report)


# Schedule the nutrition scraping task
scheduler = BackgroundScheduler()
scheduler.add_job(func=scrape_nutrition_daily, trigger="interval", days=1)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(scheduler.shutdown)


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
        todays_date = datetime.today()

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


def main():
    '''
    main method for testing
    '''
    scrape_nutrition_daily()
    # database._delete_rows(database.RecipeReport)


if __name__ == '__main__':
    main()