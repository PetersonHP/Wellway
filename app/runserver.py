#!/usr/bin/env python

# runserver.py runs the web server for the Wellway web app

import argparse
import os
import routes
import sys

import dotenv

dotenv.load_dotenv()
if os.environ['SCRAPE_ON_RUN'] == 'True':
    routes.scrape_nutrition_daily()


def main():
    parser = argparse.ArgumentParser(
        description="The Wellway application")
    parser.add_argument("port", help="the port at which the server "
                        + "should listen", type=int)
    args = parser.parse_args()
    port = args.port
    try:
        routes.app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as ex:
        print(sys.argv[0] + ": " + str(ex), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
