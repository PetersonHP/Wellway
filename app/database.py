'''
Handles interactions with the Wellway database
'''

import datetime
from datetime import datetime
import json
import os
import uuid
from typing import Type

from common import log

from dotenv import load_dotenv
from flask_login import UserMixin
import pandas as pd
import sqlalchemy
from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, JSON, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from werkzeug.security import generate_password_hash, check_password_hash


load_dotenv()

# set to True if using a locally running PostgreSQL database for debugging
LOCAL_DB = False

if LOCAL_DB:
    _DATABASE_URL = os.environ['INTERNAL_DB_URL']
else:
    _DATABASE_URL = os.environ['EXTERNAL_DB_URL']

log.info('Searching for DB at %s', _DATABASE_URL)

_engine = sqlalchemy.create_engine(_DATABASE_URL)


class Base(DeclarativeBase):
    '''
    sqlalchemy DeclarativeBase class
    '''


class RecipeReport(Base):
    '''
    Recipe_Reports rows each represent a menu item at a specific dining hall, 
    for a specific meal, for a specific day. These rows include all of the 
    nutritional information provided by menus.princeton.edu
    '''
    __tablename__ = 'recipe_reports'

    report_id = Column(UUID(as_uuid=True),
                       primary_key=True, default=uuid.uuid4)

    report_date = Column(Date, nullable=False)
    report_location = Column(String(255), nullable=False)
    report_meal = Column(String(255), nullable=False)

    recipe_name = Column(String(255), nullable=False)
    portion_info = Column(String(255), nullable=False)

    protein = Column(Float)
    fat = Column(Float)
    carbs = Column(Float)
    fiber = Column(Float)
    potassium = Column(Float)
    cholesterol = Column(Float)
    calories = Column(Float)
    sugar = Column(Float)
    sodium = Column(Float)
    vitamin_a = Column(Float)
    vitamin_b = Column(Float)


class User(Base, UserMixin):
    '''
    Users tracks users of the app. This will likely be updated in the future 
    to enable authentication via Google CAS and or university CAS systems.
    '''
    __tablename__ = 'users'

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255))
    created_at = Column(TIMESTAMP, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    def get_id(self):
        return str(self.user_id)


class FoodLog(Base):
    '''
    Food_logs link users to recipe reports on each day.
    This allows a user to track what they ate in a day and see the nutrition info. 
    '''
    # https://www.nal.usda.gov/programs/fnic#:~:text=How%20many%20calories%20are%20in,provides%209%20calories%20per%20gram.
    CALS_PER_GRAM = {
        'carbs': 4,
        'protein': 4,
        'fat': 9
    }

    __tablename__ = 'food_logs'

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    log_date = Column(Date, nullable=False)
    user_id = Column(UUID(as_uuid=True),
                     ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)

    log = Column(JSON, nullable=False)

    user = relationship("User", backref="food_logs")

    def get_summary(self) -> dict:
        '''
        Returns a nutrition summary dict structured as follows:

        {
            'total_calories': int,

            'grams_protein': int,
            'grams_fat': int,
            'grams_carbs': int,

            'percent_protein': float,
            'percent_fat': float,
            'percent_carbs': float
        }
        '''
        result = {
            'total_calories': 0,

            'grams_protein': 0,
            'grams_fat': 0,
            'grams_carbs': 0,

            'percent_protein': 0,
            'percent_fat': 0,
            'percent_carbs': 0
        }

        this_log = json.loads(self.log)
        with sqlalchemy.orm.Session(_engine) as session:
            try:
                for _, recipes in this_log['meals'].items():
                    for report_tuple in recipes:
                        report = session.get(RecipeReport, report_tuple[0])
                        qty = report_tuple[1]

                        if report.calories is not None:
                            result['total_calories'] += int(report.calories) * qty
                        if report.protein is not None:
                            result['grams_protein'] += int(report.protein) * qty
                        if report.fat is not None:
                            result['grams_fat'] += int(report.fat) * qty
                        if report.carbs is not None:
                            result['grams_carbs'] += int(report.carbs) * qty

                if result['total_calories'] > 0:
                    result['percent_protein'] = result['grams_protein'] * \
                        self.CALS_PER_GRAM['protein'] / \
                        result['total_calories']
                    result['percent_fat'] = result['grams_fat'] * \
                        self.CALS_PER_GRAM['fat'] / result['total_calories']
                    result['percent_carbs'] = result['grams_carbs'] * \
                        self.CALS_PER_GRAM['protein'] / \
                        result['total_calories']

                return result

            except Exception as e:
                raise e

    def get_full_report(self):
        '''
        Returns the full report of all nutritional information for this log
        '''
        # TODO: implement


def store_nut_rpt(location: str, meal: str, date: datetime, report: pd.DataFrame) -> None:
    '''
    stores new recipe reports in the database based on a nutrition report passed in
    '''
    new_rows = []
    for _, row in report.iterrows():
        new_rows.append(RecipeReport(
            report_id=uuid.uuid4(),

            report_date=date,
            report_location=location.lower(),
            report_meal=meal.lower(),

            recipe_name=row['Recipe Name'],
            portion_info=row['Portion'],
            protein=row['Protein (g)'] if pd.notna(
                row['Protein (g)']) else None,
            fat=row['Fat-T (g)'] if pd.notna(row['Fat-T (g)']) else None,
            carbs=row['Carbohydrates (g)'] if pd.notna(
                row['Carbohydrates (g)']) else None,
            fiber=row['Fiber (g)'] if pd.notna(row['Fiber (g)']) else None,
            potassium=row['Potassium (mg)'] if pd.notna(
                row['Potassium (mg)']) else None,
            cholesterol=row['Cholesterol (mg)'] if pd.notna(
                row['Cholesterol (mg)']) else None,
            calories=row['Calories (kcal)'] if pd.notna(
                row['Calories (kcal)']) else None,
            sugar=row['Sugar (g)'] if pd.notna(row['Sugar (g)']) else None,
            sodium=row['Sodium (mg)'] if pd.notna(
                row['Sodium (mg)']) else None,
            vitamin_a=row['Vitamin A (IU)'] if pd.notna(
                row['Vitamin A (IU)']) else None,
            vitamin_b=row['Vitamin C (mg)'] if pd.notna(
                row['Vitamin C (mg)']) else None,
        ))

    with sqlalchemy.orm.Session(_engine) as session:
        try:
            session.add_all(new_rows)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e


def get_stored_menu(location: str, meal: str, date: datetime) -> list[tuple[str, str, str]]:
    '''
    Returns a list of menu items for a provided [location], [meal], and [date].

    List items are tuples of the format (report_id, recipe_name, portion_info).
    '''
    result = []
    today = date.strftime('%Y-%m-%d')
    lower_meal = meal.lower()
    with sqlalchemy.orm.Session(_engine) as session:
        items = session.query(RecipeReport).filter(
            RecipeReport.report_date == today,
            RecipeReport.report_location == location,
            RecipeReport.report_meal == lower_meal
        ).all()

        for item in items:
            result.append(
                (str(item.report_id), item.recipe_name, item.portion_info))

    return result


def register_user(username: str, email: str, password: str, timestamp: datetime) -> UUID | None:
    '''
    Attempts to register a new user. 

    Returns the new user_id if successful or None if the user already exists. 

    Raises an exception if there is a database problem.
    '''
    new_user = User(
        user_id=uuid.uuid4(),
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        created_at=timestamp,
    )

    with sqlalchemy.orm.Session(_engine) as session:
        existing_user = session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            return None

        try:
            session.add(new_user)
            session.commit()
            return new_user.user_id
        except Exception as e:
            session.rollback()
            raise e


def validate_user(username: str, password: str) -> User | None:
    '''
    Validates a given username and password combo.

    If the combo is valid, returns the User. Otherwise returns None.
    '''
    with sqlalchemy.orm.Session(_engine) as session:
        user = session.query(User).filter(User.username == username).first()

        if user and check_password_hash(user.password_hash, password):
            return user

        return None


def get_user_by_id(user_id: str) -> User | None:
    '''
    Returns the User object corresponding to the provided user_id

    Returns None if the user doesn't exist
    '''
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        # invalid uuid
        return None

    with sqlalchemy.orm.Session(_engine) as session:
        try:
            result = session.get(User, user_uuid)
            return result
        except Exception:
            # user not found
            return None


def _get_create_food_log(
        user: User,
        timestamp: datetime,
        session: sqlalchemy.orm.Session
) -> FoodLog:
    '''
    Gets the food log for [user] for the day of the [day_timestamp].

    Creates an empty log if none exist for this user on this day.

    Log JSON Schema:
    {
        user_id: uuid str,
        log_date: datetime str ('%Y-%m-%d'),

        meals: {
            breakfast: list[(RecipeReport uuid str, quantity int)],
            lunch: list[(RecipeReport uuid str, quantity int)],
            dinner: list[(RecipeReport uuid str, quantity int)],
            snacks: list[(RecipeReport uuid str, quantity int)]
        }
    }
    '''
    day = timestamp.strftime('%Y-%m-%d')

    result = session.query(FoodLog).filter(
        FoodLog.user_id == user.user_id,
        FoodLog.log_date == day
    ).first()

    if result is None:
        # create new log
        result = FoodLog(
            log_id=uuid.uuid4(),
            log_date=day,
            user_id=user.user_id,

            log=json.dumps({
                'user_id': str(user.user_id),
                'log_date': day,

                'meals': {
                    'breakfast': [],
                    'lunch': [],
                    'dinner': [],
                    'snacks': []
                }
            })
        )
        session.add(result)
        session.commit()
        session.refresh(result)

    _ = result.log
    return result


def get_create_food_log(user: User, timestamp: datetime):
    '''
    public facing version of _get_create_food_log
    '''
    with sqlalchemy.orm.Session(_engine) as session:
        try:
            return _get_create_food_log(user, timestamp, session)
        except Exception as e:
            session.rollback()
            raise e


def add_foods_to_log(user: User, meal: str, timestamp: datetime, recipes: list[(str, int)]):
    '''
    Adds a list of recipes to a users daily food log

    List item format: (recipe_id, quantity)
    '''

    with sqlalchemy.orm.Session(_engine) as session:
        try:
            current_log = _get_create_food_log(user, timestamp, session)
            log_dict = json.loads(current_log.log)

            lower_meal = meal.lower()
            for recipe_id in recipes:
                log_dict['meals'][lower_meal].append(recipe_id)

            current_log.log = json.dumps(log_dict)
            session.commit()

        except Exception as e:
            session.rollback()
            raise e


def _delete_food_log(user: User, date: datetime):
    '''
    Deletes a daily food log
    '''
    today = date.strftime('%Y-%m-%d')
    with sqlalchemy.orm.Session(_engine) as session:
        try:
            to_delete = session.query(FoodLog).filter(
                FoodLog.user_id == user.user_id,
                FoodLog.log_date == today
            ).first()

            session.delete(to_delete)
            session.commit()

        except Exception as e:
            session.rollback()
            raise e


def _delete_rows(model: Type[Base]) -> None:
    '''
    Deletes all rows from the table corresponding to [model]
    '''
    with sqlalchemy.orm.Session(_engine) as session:
        try:
            session.query(model).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


def main():
    '''
    main method for testing purposes
    '''

    # _delete_rows(FoodLog)
    # tiger = get_user_by_id('73fde1ce-5888-4999-a647-8ac68a9755ab')
    # food = get_create_food_log(tiger, datetime.now())
    # add_foods_to_log(
    #     tiger,
    #     'dinner',
    #     datetime.now(),
    #     [('81dc6102-c473-4b6e-911d-81250518c845', 2)]
    # )

    # print(food.get_summary())


if __name__ == '__main__':
    main()
