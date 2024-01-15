# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
import geocoder
import requests
from odoo import http
from odoo.http import request


class WeatherNotification(http.Controller):
    """
    Controller class for fetching weather details based on location.
    This class provides a controller to fetch weather information based on the
    user's location setting.
    It supports both automatic and manual location settings.
    """

    @http.route('/weather/notification/check', type='json', auth="public",
                methods=['POST'])
    def weather_notification(self):
        """
        Controller for fetching weather data
        :return: Dictionary of weather information
        :rtype: dict
        """
        weather_data = {'data': False}
        if request.env.user.api_key:
            if request.env.user.location_set == 'auto':
                try:
                    response = geocoder.ip('me')
                    if response.status_code == 200:
                        lat = round(response.latlng[0], 2)
                        lng = round(response.latlng[1], 2)
                        url = 'https://api.openweathermap.org/data/2.5' \
                              f'/weather?lat={lat}&lon={lng}&appid={request.env.user.api_key}'
                        weather = requests.get(url, timeout=20)
                        if weather.status_code == 200:
                            weather_data = weather.json()
                except Exception:
                    pass
            elif request.env.user.location_set == 'manual':
                try:
                    url = 'https://api.openweathermap.org/data/2.5' \
                          f'/weather?q={request.env.user.city}&appid={request.env.user.api_key}'
                    city_req = requests.get(url, timeout=20)
                    if city_req.status_code == 200:
                        weather_data = city_req.json()
                except Exception:
                    pass
        return weather_data
