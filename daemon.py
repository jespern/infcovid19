import time
import toml
import requests

from datetime import datetime

from influxdb import InfluxDBClient

CONST_BASE_URL = 'https://api.covid19api.com'
CONST_COUNTRY_URL = CONST_BASE_URL + '/total/country'
CONST_CFG_FN = 'config.toml'

if __name__ == '__main__':
    delay = 60
    config = {}

    with open(CONST_CFG_FN) as fp:
        config = toml.load(fp)
        delay = int(config['delay'])

    client = InfluxDBClient('172.16.1.56', 8086, 'username', 'password', 'telegraf')
    client.create_database('covid19')

    while True:
        now = datetime.utcnow()

        req = requests.get(CONST_BASE_URL+'/summary')
        resp = req.json()

        if 'Global' in resp.keys():
            gbl = resp['Global']
            data = {
                'confirmed': gbl['TotalConfirmed'],
                'deaths': gbl['TotalDeaths'],
                'recovered': gbl['TotalRecovered'],
            }

            json_body = [
                {
                    "measurement": "covid19_global",
                    "tags": {},
                    "time": now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "fields": data,
                }
            ]

            print(json_body)

            client.write_points(json_body)        

        bodies = []

        for country in ['denmark', 'united-states', 'spain', 'italy', 
                        'germany', 'france', 'united-kingdom', 'china', 
                        'iran', 'sweden', 'korea-south', 'brazil']:
            req = requests.get(CONST_COUNTRY_URL + '/' + country)

            for dp in req.json():
                bodies += [
                    {
                        "measurement": "covid19_country",
                        "tags": {
                            "country": dp["Country"],
                        },
                        "time": dp["Date"],
                        "fields": {
                            "confirmed": dp["Confirmed"],
                            "deaths": dp["Deaths"],
                            "recovered": dp["Recovered"],
                            "active": dp["Active"],
                        }
                    }
                ]

            client.write_points(bodies)

        time.sleep(delay)