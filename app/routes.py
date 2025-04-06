'''
Handle client http requests
'''

import atexit
from datetime import datetime
import logging
import os
import uuid

from common import DINING_HALLS, MEALS
import database
from database import User
from forms import RegistrationForm, LoginForm, ForgotPasswordForm
import scraper

from apscheduler.schedulers.background import BackgroundScheduler
import dotenv
import flask
from flask import Flask
import flask_login
from flask_login import LoginManager

# initialization code
dotenv.load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']

login_manager = LoginManager()
login_manager.init_app(app)

log = logging.getLogger(__name__)
logging.basicConfig(filename=f'{os.path.dirname(os.path.abspath(__file__))}' +
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


# authentication stuff
@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    return database.get_user(user_id)


@app.route('/', methods=['GET'])
def index():
    '''
    displays the home screen for the app
    '''
    return flask.make_response(flask.render_template('index.html'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    '''
    login as an existing user
    '''
    form = LoginForm(flask.request.form)
    if form.validate_on_submit():
        # Login and validate the user.
        # user should be an instance of your `User` class
        # TODO: implement
        flask_login.login_user(user)

        flask.flash('Logged in successfully.')

        next_page = flask.request.args.get('next')
        return flask.redirect(next_page or flask.url_for('index'))
    
    return flask.render_template('login.html', form=form)


@app.route('/register')
def register():
    '''
    register as a new user
    '''
    # TODO: implement
    form = RegistrationForm(flask.request.form)
    return flask.render_template('forms/register.html', form=form)


@app.route('/forgot')
def forgot():
    '''
    handle a forgotten password
    '''
    # TODO: implement
    form = ForgotPasswordForm(flask.request.form)
    return flask.render_template('forms/forgot.html', form=form)


# @app.route('/getReport', methods=['POST'])
# def get_report():
#     '''
#     displays the nutrition report for the requested meal
#     '''
#     try:
#         location = flask.request.form.get('location')
#         meal = flask.request.form.get('meal')
#         todays_date = datetime.today()

#         nut_rpt = scraper.get_meal_info(location, meal, todays_date)

#         rendered = flask.render_template(
#             'report.html',
#             content=nut_rpt.to_html(
#                 classes="table table-striped", index=False),
#             location=DHALL_ARGS[location][1],
#             meal=meal
#         )
#         return flask.make_response(rendered)
#     except Exception as ex:
#         print(sys.argv[0] + ": " + str(ex), file=sys.stderr)
#         return 'Internal server error occurred. Please contact the site admin.'


def main():
    '''
    main method for testing
    '''
    # scrape_nutrition_daily()
    # database._delete_rows(database.RecipeReport)


if __name__ == '__main__':
    main()
