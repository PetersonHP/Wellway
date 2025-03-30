import argparse
import requests
from bs4 import BeautifulSoup
import datetime
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

def main():
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
    meal=args.meal
    todays_date = datetime.date.today()

    if DHALL_ARGS[location] is None:
        raise ValueError(f'Invalid location {location}. ' +
                         "Valid locations include 'cjl', 'forbes', 'roma', 'whitman', and 'yeh'.")

    if meal != 'Breakfast' and meal != 'Lunch' and meal != 'Dinner':
        raise ValueError(f'Invalid meal {meal}. +'
                         'Valid meals include \'Breakfast\', \'Lunch\', and \'Dinner\'.')

    # construct the query
    query_args = {
        'locationNum': DHALL_ARGS[location][0],
        'locationName': DHALL_ARGS[location][1],
        'dtdate': todays_date.strftime("%m/%d/%y"),
        'mealName': meal,
        'Name': 'Princeton University Campus Dining'
        }
    full_url = f'{CAMPUS_DINING_URL}?{urllib.parse.urlencode(query_args)}'

    # retrieve the meal data
    response = requests.get(full_url, headers={'User-Agent': 'Mozilla/5.0'}) # TODO: add a timeout to this request
    soup = BeautifulSoup(response.text, 'html.parser')
    menu_table = soup.find('table', {'id': 'pickMenuTable'})

    print(f'{location} {meal} menu for {todays_date.strftime("%m/%d/%y")}:')
    for item in menu_table.find_all('a', {'onmouseover': "window.status = 'Click for label of this item.'; return true;"}):
        print(item.get_text(strip=True))


if __name__ == '__main__':
    main()
