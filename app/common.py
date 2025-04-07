'''
Common utilities for the Wellway app
'''

from datetime import datetime
import logging
import os


CJL = 'cjl'
FORBES = 'forbes'
GRAD_COLLEGE = 'gradcollege'
ROMA = 'roma'
WHITMAN = 'whitman'
YEH_NCW = 'yeh'

DINING_HALLS = [CJL, FORBES, GRAD_COLLEGE, ROMA, WHITMAN, YEH_NCW]

DHALL_ARGS = {
    'cjl': ['05', 'Center for Jewish Life'],
    'forbes': ['03', 'Forbes College'],
    'gradcollege': ['04', 'Graduate College'],
    'roma': ['01', 'Rockefeller & Mathey Colleges'],
    'whitman': ['08', 'Whitman College & Butler College'],
    'yeh': ['06', 'Yeh College & New College West']
}

BREAKFAST = 'Breakfast'
LUNCH = 'Lunch'
DINNER = 'Dinner'

MEALS = [BREAKFAST, LUNCH, DINNER]


log = logging.getLogger('Wellway')
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
logging.basicConfig(filename=f'{os.path.dirname(os.path.abspath(__file__))}' +
                    f'/logs/wellway-{timestamp}.log',
                    level=logging.INFO)
