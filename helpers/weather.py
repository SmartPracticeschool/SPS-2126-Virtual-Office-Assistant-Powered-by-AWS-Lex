# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License"). You may not
# use this file except in compliance with the License. A copy of the
# License is located at:
#    http://aws.amazon.com/asl/
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, expressi
# or implied. See the License for the specific language governing permissions 
# and limitations under the License.

import requests
import json
from helpers.config import ConfigHelper
import logging


class Weather(object):
    def __init__(self, **kwargs):
        c = ConfigHelper().config
        if 'wunderground_api_key' not in c.keys() or \
                'weather_state' not in c.keys() or \
                'weather_city' not in c.keys():
            logging.warning('Config file missing wunderground_api_key, ' +
                            'weather_state, or weather_city')
            return

        self.api_key = kwargs.get('ApiKey', c["wunderground_api_key"])
        self.state = kwargs.get('State', c["weather_state"])
        self.city = kwargs.get('City', c["weather_city"])
        logging.info('Weather state={}, city={}'.format(self.state, self.city))

    def get_feel(self, temp):
        print 'temp is {}'.format(temp)
        if temp > 80:
            feel = "hot"
            in_clothes = "shorts and a t-shirt"
            out_clothes = "no coat or jacket"
        elif temp > 70:
            feel = "warm"
            in_clothes = "jeans and a t-shirt and socks"
            out_clothes = "no coat or jacket"
        elif temp > 60:
            feel = "cool"
            in_clothes = "jeans and a t-shirt and socks"
            out_clothes = "a jacket"
        elif temp > 50:
            feel = "kinda cold"
            in_clothes = "jeans and a long-sleeve shirt and socks"
            out_clothes = "a warm coat"
        else:
            feel = "very cold"
            in_clothes = "jeans and a long-sleeve shirt and socks"
            out_clothes = "a warm coat"

        return feel, in_clothes, out_clothes

    def get_forecast(self):
        j = self.make_request('forecast')
        print j
        t = j["forecast"]["simpleforecast"]["forecastday"][0]
        self.f_high = int(t["high"]['fahrenheit'])
        self.f_low = int(t["low"]['fahrenheit'])
        self.f_weather = t["conditions"]
        self.f_feel, self.f_in, self.f_out = self.get_feel(self.f_high)

    def get_conditions(self):
        j = self.make_request('conditions')
        self.c_weather = j["current_observation"]["weather"]
        self.c_temp = int(j["current_observation"]["temp_f"])
        self.c_feel, self.c_in, self.c_out = self.get_feel(self.c_temp)

    def describe(self):
        self.get_forecast()
        self.get_conditions()
        t = """
            Right now, the weather is {}. The temperature is {}, which means
            that it is {} right now. Today, the weather will be {} and the
            temperature will be {} which means that you will need to wear
            {} if you go outside. I suggest that you wear {} today.
            """
        return t.format(self.c_weather, self.c_temp, self.c_feel,
                        self.f_weather, self.f_feel, self.f_out,
                        self.f_in)

    def make_request(self, ft):
        w = "http://api.wunderground.com/api/" + \
            "{}/{}/q/{}/{}.json".format(self.api_key, ft, self.state,
                                        self.city)
        r = requests.get(w)
        j = json.loads(r.text)
        return j
