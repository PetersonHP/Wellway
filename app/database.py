'''
Handles interactions with the Wellway database
'''

import datetime
import os
import uuid
from typing import Type

import scraper

from dotenv import load_dotenv
import pandas as pd
import sqlalchemy
from sqlalchemy import Column, Date, Float, ForeignKey, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


load_dotenv()

# set to True if using a locally running PostgreSQL database for debugging
LOCAL_DB = True

if LOCAL_DB:
    _DATABASE_URL = os.environ['INTERNAL_DB_URL']
else:
    _DATABASE_URL = os.environ['EXTERNAL_DB_URL']

_engine = sqlalchemy.create_engine(_DATABASE_URL)


class Base(DeclarativeBase):
    '''
    sqlalchemy DeclarativeBase class
    '''
    pass


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


class User(Base):
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


class FoodLog(Base):
    '''
    Food_logs link users to recipe reports on each day.
    This allows a user to track what they ate in a day and see the nutrition info. 
    '''
    __tablename__ = 'food_logs'

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey(
        'users.user_id', ondelete='CASCADE'), nullable=False)
    report_id = Column(UUID(as_uuid=True), ForeignKey(
        'recipe_reports.report_id'), nullable=False)
    log_date = Column(Date, nullable=False)


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
    location = 'roma'
    meal = 'Dinner'
    todays_date = datetime.date.today()

    nut_rpt = scraper.get_meal_info(location, meal, todays_date)
    store_nut_rpt(location, meal, todays_date, nut_rpt)

    with sqlalchemy.orm.Session(_engine) as session:
        result = session.query(RecipeReport)
        print(result.all())

    _delete_rows(RecipeReport)


if __name__ == '__main__':
    main()
