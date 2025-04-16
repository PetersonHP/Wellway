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
from forms import RegistrationForm, LoginForm, AddFoodForm, EditLogForm
import princeton_cas
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
                try:
                    database.store_nut_rpt(hall, meal, todays_date, report)
                except Exception as e:
                    print(e)


# scrape on run if necessary
if os.environ['SCRAPE_ON_RUN'] == 'True':
    scrape_nutrition_daily()


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
    displays the login screen if the user is not authenticated and the dashboard if they are
    '''
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for('dashboard'))

    return flask.make_response(flask.render_template('index.html'))


@app.route('/dashboard', methods=['GET'])
def dashboard():
    '''
    dashboard home screen for a user
    '''
    if not flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for('index'))

    current_log = database.get_create_food_log(
        flask_login.current_user, datetime.now())
    daily_summary = current_log.get_summary()

    return flask.render_template('dashboard.html', daily_summary=daily_summary)


@app.route('/fullReport')
@login_required
def full_report():
    '''
    full nutritional report screen for a user
    '''
    current_log = database.get_create_food_log(
        flask_login.current_user, datetime.now())
    daily_report = current_log.get_full_report()
    return flask.render_template('fullReport.html', report=daily_report)


@app.route('/viewEditLog', methods=['GET', 'POST'])
@login_required
def view_edit_log():
    '''
    Displays and allows for editing of today's log
    '''
    current_log = database.get_create_food_log(
        flask_login.current_user, datetime.now())

    entries = current_log.get_full_log()

    form = EditLogForm(flask.request.form)

    for entry in entries:
        form.add_item(entry[1])
    recipes_with_log = zip(form.recipes, entries)

    if form.validate_on_submit():
        for recipe_form, _ in recipes_with_log:
            if recipe_form.selected.data:
                current_log.remove_recipe_by_id(recipe_form.recipe_id.data)

        return flask.redirect(flask.url_for('dashboard'))

    # Organize entries by meal for display, matching with indexed form field
    meals = ['breakfast', 'lunch', 'dinner', 'snacks']
    meal_items = {meal: [] for meal in meals}

    for field, entry in recipes_with_log:
        meal = entry[0]
        recipe_id = entry[1]
        recipe_name = entry[2]
        portion_info = entry[3]
        qty = entry[4]
        cals = entry[5]
        protein = entry[6]
        fat = entry[7]
        carbs = entry[8]

        meal_items[meal].append({
            'id': recipe_id,
            'recipe_name': recipe_name,
            'portion_info': portion_info,
            'qty': qty,
            'cals': cals,
            'protein': protein,
            'fat': fat,
            'carbs': carbs,
            'field': field
        })

    return flask.render_template('viewEditLog.html', form=form, meal_items=meal_items)


@app.route('/signout', methods=['GET'])
@login_required
def signout():
    '''
    signs out the currently signed in user
    '''
    flask_login.logout_user()
    return flask.redirect(flask.url_for('index'))


@app.route('/login/cas')
def login_cas():
    '''
    Handles Princeton CAS login and optional auto-registration
    '''
    cas_client = princeton_cas.CASClient()
    username = cas_client.authenticate()  # Redirects if no ticket or invalid

    user = database.get_user_by_name(username)
    if user:
        flask_login.login_user(user)
        log.info('CAS login success for %s', username)
        return flask.redirect(flask.url_for('dashboard'))

    # Auto-register if not already in database
    new_id = database.register_user(
        username, f'{username}@princeton.edu', None, datetime.now())

    if not new_id:
        flask.flash('Account creation failed for CAS user.')
        return flask.redirect(flask.url_for('index'))

    flask_login.login_user(load_user(str(new_id)))
    return flask.redirect(flask.url_for('dashboard'))


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


@app.route('/deleteLog', methods=['POST'])
@login_required
def delete_log():
    '''
    Deletes todays log for the logged in user
    '''
    database._delete_food_log(flask_login.current_user, datetime.now())
    return flask.redirect(flask.url_for('dashboard'))


@app.route('/comingSoon', methods=['GET'])
def coming_soon():
    return flask.render_template('comingSoon.html')

# @app.route('/forgot')
# def forgot():
#     '''
#     handle a forgotten password
#     '''
#     # TODO: implement
#     form = ForgotPasswordForm(flask.request.form)
#     return flask.render_template('forgot.html', form=form)


def main():
    '''
    main method for testing
    '''
    scrape_nutrition_daily()


if __name__ == '__main__':
    main()
