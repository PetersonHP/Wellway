'''
Handle client http requests
'''

from apscheduler.triggers.cron import CronTrigger
import atexit
from datetime import datetime
import os

from common import DINING_HALLS, DHALL_ARGS, MEALS, log
import database
from database import User
from forms import RegistrationForm, LoginForm, AddFoodForm
import scraper

from apscheduler.schedulers.background import BackgroundScheduler
import dotenv
import flask
from flask import Flask
import flask_login
from flask_login import LoginManager, login_required

# initialization code
dotenv.load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']

login_manager = LoginManager()
login_manager.init_app(app)


# track the last time nutrition info was scraped
nutrition_last_updated = ''


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
scheduler.add_job(
    func=scrape_nutrition_daily,
    trigger=CronTrigger(hour=6, minute=0)  # Runs daily at 6:00 AM
)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(scheduler.shutdown)


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    '''
    load_user function for flask_login
    '''
    return database.get_user_by_id(user_id)


@app.route('/', methods=['GET'])
def index():
    '''
    displays the home screen for the app
    '''
    return flask.make_response(flask.render_template('index.html'))


@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    '''
    dashboard home screen for a user
    '''
    current_log = database.get_create_food_log(
        flask_login.current_user, datetime.now())
    daily_summary = current_log.get_summary()

    return flask.render_template('dashboard.html', daily_summary=daily_summary)


@app.route('/signout', methods=['GET'])
@login_required
def signout():
    '''
    signs out the currently signed in user
    '''
    flask_login.logout_user()
    return flask.redirect(flask.url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    '''
    login as an existing user
    '''
    form = LoginForm(flask.request.form)
    if form.validate_on_submit():
        current_user = database.validate_user(
            form.username.data, form.password.data)
        if not current_user:
            # FAIL
            log.info('Failed to login user %s', form.username)
            flask.flash('Incorrect username or password.')
            return flask.render_template('loginPage.html', form=form)

        # SUCCESS
        flask_login.login_user(current_user)
        log.info('Successfully logged in user %s', form.username)

        return flask.redirect(flask.url_for('dashboard'))

    return flask.render_template('loginPage.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    '''
    register as a new user
    '''
    form = RegistrationForm(flask.request.form)
    if form.validate_on_submit():
        new_id = database.register_user(form.username.data,
                                        form.email.data,
                                        form.password.data,
                                        datetime.now()
                                        )
        if not new_id:
            flask.flash(f'User with name {form.username.data} and or ' +
                        f'email {form.email.data} is already registered.')
            return flask.render_template('registerPage.html', form=form)
        else:
            flask_login.login_user(load_user(str(new_id)))

            return flask.redirect(flask.url_for('dashboard'))

    return flask.render_template('registerPage.html', form=form)


@app.route('/addFood/', methods=['GET', 'POST'])
@login_required
def add_food(location=None, meal=None):
    '''
    Add new foods to today's log
    '''
    location = flask.request.args.get('location', None)
    meal = flask.request.args.get('meal', None)

    if location is None:
        return flask.render_template('selectLocation.html', DHALL_ARGS=DHALL_ARGS)
    if meal is None:
        return flask.render_template('selectMeal.html', location=location)

    menu = database.get_stored_menu(location, meal, datetime.now())
    form = AddFoodForm(flask.request.form)
    for _ in range(len(menu)):
        form.add_item()
    items_with_menu = zip(form.items, menu)

    if form.validate_on_submit():
        food_to_add = []
        for item_form, menu_item in items_with_menu:
            if item_form.quantity.data > 0:
                food_to_add.append((menu_item[0], item_form.quantity.data))

        database.add_foods_to_log(
            flask_login.current_user, meal, datetime.now(), food_to_add
        )
        return flask.redirect(flask.url_for('dashboard'))

    return flask.render_template(
        'addFood.html',
        menu=menu, form=form, items_with_menu=items_with_menu,
        location=location, meal=meal
    )


@app.route('/viewEditLog/', methods=['GET', 'POST'])
@login_required
def view_edit_log():
    '''
    View or edit the food log for today
    '''
    return flask.render_template('viewEditLog.html')

@app.route('/deleteLog', methods=['POST'])
@login_required
def delete_log():
    '''
    Deletes todays log for the logged in user
    '''
    database._delete_food_log(flask_login.current_user, datetime.now())
    return flask.redirect(flask.url_for('dashboard'))


# @app.route('/forgot')
# def forgot():
#     '''
#     handle a forgotten password
#     '''
#     # TODO: implement
#     form = ForgotPasswordForm(flask.request.form)
#     return flask.render_template('forgot.html', form=form)


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
    scrape_nutrition_daily()


if __name__ == '__main__':
    main()
