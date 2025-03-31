'''
scraper.py handles the scraping of nutrition information for menu items 
during meals at various Princeton University dining halls from menus.princeton.edu
'''

import datetime
import urllib

from common import DHALL_ARGS

from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


CAMPUS_DINING_URL = 'https://menus.princeton.edu/dining/_Foodpro/online-menu/pickMenu.asp'
CAMPUS_DINING_ENC = 'ISO-8859-1'


def _get_dining_url(location: str, meal: str, time: datetime) -> str:
    '''
    returns the url to get the menu for [meal] at [location] at [time] 
    from menus.princeton.edu'
    '''

    query_args = {
        'locationNum': DHALL_ARGS[location][0],
        'locationName': DHALL_ARGS[location][1],
        'dtdate': time.strftime("%m/%d/%y"),
        'mealName': meal,
        'Name': 'Princeton University Campus Dining'
    }
    return f'{CAMPUS_DINING_URL}?{urllib.parse.urlencode(query_args)}'


def _get_nut_rpt(form_url: str) -> str:
    '''
    fills out the menu form to request a nutrition report for one of each item
    returns the resulting report from campus dining
    '''

    driver = webdriver.Chrome()

    driver.get(form_url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "pickMenuTable"))
    )

    # check boxes
    checkboxes = driver.find_elements(By.NAME, "recipe")
    for box in checkboxes:
        if not box.is_selected():
            box.click()

    # submit form
    submit = driver.find_element(By.XPATH, "//input[@type='submit']")
    submit.click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "nutrptbody"))
    )

    raw_report = driver.page_source
    driver.quit()

    return raw_report


def _parse_nut_rpt(raw: str) -> pd.DataFrame | None:
    '''
    Parses a raw html nutrition report into a dataframe
    '''
    new_rows = {
        'Recipe Name': [],
        'Portion': [],
        'Protein (g)': [],
        'Fat-T (g)': [],
        'Carbohydrates (g)': [],
        'Fiber (g)': [],
        'Potassium (mg)': [],
        'Cholesterol (mg)': [],
        'Calories (kcal)': [],
        'Sugar (g)': [],
        'Sodium (mg)': [],
        'A-IU (IU)': [],
        'Vitamin C (mg)': []
    }

    # hardcoded character replacement fix for encoding issues -
    # this is an ugly and unscalable solution, so we should figure
    # out a better way
    fixes = {
        # 'Θ': 'é',
        # 'á': ' ',
        '\n': ''
    }

    soup = BeautifulSoup(raw, 'html5lib')   # DEBUG
    nutrition_data_raw = soup.find_all('table')[1]

    for row in nutrition_data_raw.find_all('tr'):
        # skip rows with head columns
        if row.find('td', {'class': 'nutrptmainheadcolumns'}) or \
                row.find('td', {'class': 'nutrptunitheadcolumns'}) or \
                row.find('div', {'class': 'nutrpttotalheader'}):
            continue

        # extract data from row
        str_vals = [row.find('div', {'class': 'nutrptnames'}),
                    row.find('div', {'class': 'nutrptportions'})
                    ]
        float_vals = row.find_all('div', {'class': 'nutrptvalues'})
        nut_vals = str_vals + float_vals

        # put extracted data into df construction dict
        col = 0
        for col_name, _ in new_rows.items():
            # process text
            val = nut_vals[col].get_text()
            if val == '-\xa0-\xa0-\xa0-\xa0-':
                val_processed = ''
            elif col < 2:
                val_processed = str(val)
                # ugly hardcoded fix for erroneous encodings
                for wrong, right in fixes.items():
                    val_processed = val_processed.replace(wrong, right)
            else:
                val_processed = float(val)

            new_rows[col_name].append(val_processed)
            col += 1

    result = pd.DataFrame(new_rows)
    return result


def get_meal_info(location: str, meal: str) -> pd.DataFrame:
    '''
    prototype to get today's menu items for a dining hall and a meal
    this will eventually be converted into a method to get menu items and nutritional info'

    location: the dining hall to get the menu from 
              ('cjl', 'forbes', 'gradcollege' 'roma', 'whitman', 'yeh')

    meal: the meal to get info for ('Breakfast', 'Lunch', or 'Dinner')
    '''

    todays_date = datetime.date.today()

    if DHALL_ARGS[location] is None:
        raise ValueError(f'Invalid location \'{location}\'. ' +
                         "Valid locations include 'cjl', 'forbes', 'roma', 'whitman', and 'yeh'.")

    if meal != 'Breakfast' and meal != 'Lunch' and meal != 'Dinner':
        raise ValueError(f'Invalid meal \'{meal}\'. ' +
                         'Valid meals include \'Breakfast\', \'Lunch\', and \'Dinner\'.')

    # scrape the data
    full_url = _get_dining_url(location, meal, todays_date)
    return _parse_nut_rpt(_get_nut_rpt(full_url))
