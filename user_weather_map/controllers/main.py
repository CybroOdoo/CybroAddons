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
    """controller for fetching weather data"""

    @http.route('/weather/notification/check', type='json', auth="public",
                methods=['POST'])
    def weather_notification(self):
        """method for fetching weather data"""
        if request.env.user.location_set == 'auto' and \
                request.env.user.api_key:
            g_coder = geocoder.ip('me')
            if g_coder.status_code == 200:
                lat = round(g_coder.latlng[0], 2)
                lng = round(g_coder.latlng[1], 2)
                url = 'https://api.openweathermap.org/data/2.5/weather?lat=%s&lon=%s&appid=%s' % (
                    lat, lng, request.env.user.api_key)
                weather = requests.get(url)
                if weather.status_code == 200:
                    weather_data = weather.json()
                    return weather_data
                else:
                    weather_data = {'data': False}
                    return weather_data
        elif request.env.user.location_set == 'manual' and \
                request.env.user.api_key:
            url = 'https://api.openweathermap.org/data/2.5/weather?q=%s&appid=%s' % (
                request.env.user.city, request.env.user.api_key)
            city_req = requests.get(url)
            if city_req.status_code == 200:
                weather_data = city_req.json()
                return weather_data
            else:
                weather_data = {'data': False}
                return weather_data
        else:
            weather_data = {'data': False}
            return weather_data
