'''
scraper.py handles the scraping of nutrition information for menu items 
during meals at various Princeton University dining halls from menus.princeton.edu
'''

import datetime
import requests
import urllib

from common import DHALL_ARGS

from bs4 import BeautifulSoup
import pandas as pd


PICK_MENU_URL = 'https://menus.princeton.edu/dining/_Foodpro/online-menu/pickMenu.asp'
NUT_RPT_URL = 'https://menus.princeton.edu/dining/_Foodpro/online-menu/nutRpt.asp'
CAMPUS_DINING_ENC = 'ISO-8859-1'


def _get_dining_url(base: str, location: str, meal: str, time: datetime) -> str:
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
    return f'{base}?{urllib.parse.urlencode(query_args)}'


def _get_nut_rpt(location: str, meal: str, time: datetime) -> str:
    '''
    Fills out the menu form to request a nutrition report for one of each item.
    Returns the resulting report HTML as a string.

    Returns an empty string if information is not available for the requested meal.
    '''

    try:
        options_page = requests.get(
            _get_dining_url(PICK_MENU_URL, location, meal, time),
            timeout=10
        )
    except TimeoutError:
        return ''

    if options_page.status_code != 200:
        return ''

    options_soup = BeautifulSoup(options_page.text, 'html5lib')
    options_divs = options_soup.find_all(
        'div', {'class': 'pickmenucoldispname'})
    if len(options_divs) == 0:
        return ''

    recipe_codes = []
    for option in options_divs:
        recipe_codes.append(option.find(
            'input', {'name': 'recipe'}).get('value'))

    post_data = {
        'recipe': [],
        'QTY': [1 for _ in recipe_codes]
    }

    for recipe in recipe_codes:
        post_data['recipe'].append(recipe)

    try:
        nut_rpt = requests.post(
            _get_dining_url(NUT_RPT_URL, location, meal, time),
            data=post_data,
            timeout=10
        )
    except TimeoutError:
        return ''

    if nut_rpt.status_code != 200:
        return ''

    return nut_rpt.text


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
        'Vitamin A (IU)': [],
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

    soup = BeautifulSoup(raw, 'html5lib')
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
                val_processed = None
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


def get_meal_info(location: str, meal: str, date: datetime) -> pd.DataFrame:
    '''
    get today's nutritional info for a dining hall and a meal

    location: the dining hall to get the menu from 
              ('cjl', 'forbes', 'gradcollege' 'roma', 'whitman', 'yeh')

    meal: the meal to get info for ('Breakfast', 'Lunch', or 'Dinner')
    '''

    if DHALL_ARGS[location] is None:
        raise ValueError(f'Invalid location \'{location}\'. ' +
                         "Valid locations include 'cjl', 'forbes', 'roma', 'whitman', and 'yeh'.")

    if meal != 'Breakfast' and meal != 'Lunch' and meal != 'Dinner':
        raise ValueError(f'Invalid meal \'{meal}\'. ' +
                         'Valid meals include \'Breakfast\', \'Lunch\', and \'Dinner\'.')

    # scrape the data
    raw_report = _get_nut_rpt(location, meal, date)
    if raw_report == '':
        return pd.DataFrame()
    return _parse_nut_rpt(raw_report)


# def main():
#     '''
#     main method for testing purpose
#     '''
#     from datetime import datetime
#     print(get_meal_info('cjl', 'Lunch', datetime.now()))


# if __name__ == '__main__':
#     main()
