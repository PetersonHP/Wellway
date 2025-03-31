'''
scraper.py handles the scraping of nutrition information for menu items 
during meals at various Princeton University dining halls from menus.princeton.edu
'''

import argparse
from bs4 import BeautifulSoup
import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
import urllib


CAMPUS_DINING_URL = 'https://menus.princeton.edu/dining/_Foodpro/online-menu/pickMenu.asp'


# locationNum, locationName
DHALL_ARGS = {
    'cjl': ['05', 'Center for Jewish Life'],
    'forbes': ['03', 'Forbes College'],
    'gradcollege': ['04', 'Graduate College'],
    'roma': ['01', 'Rockefeller & Mathey Colleges'],
    'whitman': ['08', 'Whitman College & Butler College'],
    'yeh': ['06', 'Yeh College & New College West']
}


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
    driver.implicitly_wait(10)

    # check boxes
    checkboxes = driver.find_elements(By.NAME, "recipe")
    for box in checkboxes:
        if not box.is_selected():
            box.click()

    # submit form
    submit = driver.find_element(By.XPATH, "//input[@type='submit']")
    submit.click()
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.TAG_NAME, "body"))
    )

    raw_report = driver.page_source
    driver.quit()

    return raw_report


def main():
    '''
    prototype to get today's menu items for a dining hall and a meal
    this will eventually be converted into a method to get menu items and nutritional info'
    '''

    # parse and validate args
    parser = argparse.ArgumentParser(
        description="Get Princeton campus dining menus")
    parser.add_argument(
        "location", help="the dining hall to get the menu from " +
        "('cjl', 'forbes', 'roma', 'whitman', 'yeh')", type=str)
    parser.add_argument("meal", help="the meal to get info for " +
                        "('Breakfast', 'Lunch', or 'Dinner')", type=str)
    args = parser.parse_args()
    location = args.location
    meal = args.meal
    todays_date = datetime.date.today()

    if DHALL_ARGS[location] is None:
        raise ValueError(f'Invalid location {location}. ' +
                         "Valid locations include 'cjl', 'forbes', 'roma', 'whitman', and 'yeh'.")

    if meal != 'Breakfast' and meal != 'Lunch' and meal != 'Dinner':
        raise ValueError(f'Invalid meal {meal}. +'
                         'Valid meals include \'Breakfast\', \'Lunch\', and \'Dinner\'.')

    # build the URL
    full_url = _get_dining_url(location, meal, todays_date)
    soup = BeautifulSoup(_get_nut_rpt(full_url), 'html.parser')
    print(soup.prettify())


if __name__ == '__main__':
    main()
