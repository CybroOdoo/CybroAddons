# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################

import logging

import geocoder
import requests
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

WEATHER_URL = 'https://api.openweathermap.org/data/2.5/weather'


class WeatherNotification(http.Controller):
    """
    Controller class for fetching weather details based on location.
    This class provides a controller to fetch weather information based on the
    user's location setting.
    It supports both automatic and manual location settings.
    """

    @http.route('/weather/notification/check', type='jsonrpc', auth="user",
                methods=['POST'])
    def weather_notification(self):
        """
        Controller for fetching weather data
        :return: Dictionary of weather information
        :rtype: dict
        """
        weather_data = {'data': False}
        # The key is restricted to administrators; read the user's own one.
        user = request.env.user.sudo()
        api_key = (user.api_key or '').strip()
        if not api_key:
            return weather_data
        if user.location_set == 'auto':
            try:
                response = geocoder.ip('me')
                lat, lng = None, None
                if response and response.status_code == 200 and response.latlng:
                    lat = round(response.latlng[0], 2)
                    lng = round(response.latlng[1], 2)
                elif user.partner_id.city:
                    res = requests.get(WEATHER_URL, params={
                        'q': user.partner_id.city.strip(), 'appid': api_key}, timeout=10)
                    if res.status_code == 200:
                        return res.json()
                if lat is not None and lng is not None:
                    weather = requests.get(WEATHER_URL, params={
                        'lat': lat, 'lon': lng, 'appid': api_key}, timeout=10)
                    if weather.status_code == 200:
                        weather_data = weather.json()
            except Exception:  # noqa: BLE001 - the systray must not break the web client
                _logger.warning("Could not fetch the weather by location", exc_info=True)
        elif user.location_set == 'manual' and user.city:
            try:
                city_req = requests.get(WEATHER_URL, params={
                    'q': user.city.strip(), 'appid': api_key}, timeout=10)
                if city_req.status_code == 200:
                    weather_data = city_req.json()
            except Exception:  # noqa: BLE001 - the systray must not break the web client
                _logger.warning("Could not fetch the weather for %s", user.city, exc_info=True)
        return weather_data
