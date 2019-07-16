# -*- coding: utf-8 -*-
#
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nikhil krishnan(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import pytz
from pytz import timezone
from dateutil.relativedelta import relativedelta
from datetime import datetime

try:
    import pytemperature
except ImportError:
    print 'pytemperature, this python package is not available. please install by using ' \
          '==> pip install pytemperature'
    pass

try:
    import simplejson as json
except ImportError:
    import json  # noqa
import urllib

import odoo
from odoo import models, fields, api
from odoo import tools
from odoo.tools.translate import _


class UserWeatherMap(models.Model):
    _name = 'user.weather.map'

    date_weather_update = fields.Datetime(string='Last update')
    name = fields.Char(string='City Name')
    city = fields.Char(string='Original City')
    user_id = fields.Many2one('res.users', string='User Name')
    weather = fields.Char(string='Weather')
    description = fields.Char(string='Description')
    temp = fields.Char(string='Temperature')
    pressure = fields.Char(string='Pressure')
    humidity = fields.Char(string='Humidity')
    min_temp = fields.Char(string='Minimum')
    max_temp = fields.Char(string='Maximum')
    sunset = fields.Char(string='Sunset')
    sunrise = fields.Char(string='Sunrise')

    def get_weather_data(self, user_id):
        user_list = self.env['res.users'].search([('id', '=', user_id)])
        if user_list.partner_id.tz:
            rec = self.search([('user_id', '=', user_id)], limit=1)
            tz = pytz.timezone(user_list.partner_id.tz)
            now_utc = datetime.now(timezone('UTC'))
            now_pacific = now_utc.astimezone(timezone(str(tz)))
            current_time = now_pacific.strftime('%d %B %Y, %I:%M%p')
            current_date = now_pacific.strftime('%d %B %Y')
            if rec:
                current_date_time = datetime.strptime(current_time, '%d %B %Y, %I:%M%p')
                last_update = datetime.strptime(rec.date_weather_update, '%Y-%m-%d %H:%M:%S')
                new_update_allowed_time = last_update + relativedelta(minutes=1)
                if current_date_time > new_update_allowed_time:
                    get_weather = self.get_weather(user_id)
                    if get_weather:
                        if get_weather['issue'] == 'bad_request':
                            return {
                                'issue': 'Bad Request'
                            }
                        elif get_weather['issue'] == 'internet':
                            return {
                                'issue': 'Connection ERROR.!'
                            }
                        elif get_weather['issue'] == 'localization':
                            return {
                                'issue': 'longitude  and latitude or address issue.'
                            }
                        elif get_weather['issue'] == 'config':
                            return {
                                'issue': 'Weather configuration not set yet.'
                            }
                        elif get_weather['issue'] == 'timezone':
                            return {
                                'issue': 'Timezone is not available'
                            }
                        else:
                            rec = self.search([('user_id', '=', user_id)], limit=1)
                else:
                    pass

                if rec:
                    vals = {
                        'date_now': current_date,
                        'date_weather_update': rec.date_weather_update,
                        'name': rec.name,
                        'city': rec.city,
                        'user_id': rec.user_id.id,
                        'weather': rec.weather,
                        'description': rec.description,
                        'temp': rec.temp,
                        'pressure': rec.pressure,
                        'humidity': rec.humidity,
                        'min_temp': rec.min_temp,
                        'max_temp': rec.max_temp,
                        'issue': '',
                    }
                    return vals
            else:
                get_weather = self.get_weather(user_id)
                if get_weather['issue'] == 'bad_request':
                    return {
                        'issue': 'Bad Request'
                    }
                elif get_weather['issue'] == 'internet':
                    return {
                        'issue': 'Connection ERROR.!'
                    }
                elif get_weather['issue'] == 'localization':
                    return {
                        'issue': 'Set correct Location'
                    }
                elif get_weather['issue'] == 'config':
                    return {
                        'issue': 'Weather configuration not set yet.'
                    }
                elif get_weather['issue'] == 'timezone':
                    return {
                        'issue': 'Timezone is not available'
                    }
                else:
                    rec = self.search([('user_id', '=', user_id)], limit=1)
                    if rec:
                        vals = {
                            'date_now': current_date,
                            'date_weather_update': rec.date_weather_update,
                            'name': rec.name,
                            'city': rec.city,
                            'user_id': rec.user_id.id,
                            'weather': rec.weather,
                            'description': rec.description,
                            'temp': rec.temp,
                            'pressure': rec.pressure,
                            'humidity': rec.humidity,
                            'min_temp': rec.min_temp,
                            'max_temp': rec.max_temp,
                            'issue': '',
                        }
                        return vals
                    else:
                        return {
                            'issue': 'Bad request'
                        }

        else:
            return {
                'issue': 'Timezone is not available'
            }

    def get_weather(self, user_id):
        rec = self.env['user.weather.map.config'].search([('user_id', '=', user_id)], limit=1)
        if rec:
            weather_path = 'http://api.openweathermap.org/data/2.5/weather?'
            if rec.u_longitude and rec.u_latitude:
                    params = urllib.urlencode(
                        {'lat': rec.u_latitude, 'lon': rec.u_longitude, 'APPID': rec.appid})
            elif rec.city:
                params = urllib.urlencode(
                    {'q': rec.city, 'APPID': rec.appid})
            else:
                return {
                            'issue': 'localization'
                        }

            url = weather_path + params
            try:
                f = urllib.urlopen(url)
            except Exception:
                f = False
            if f:
                ret = f.read().decode('utf-8')
                result = json.loads(ret)
                if result:
                    if "cod" in result.keys():
                        if result['cod'] == 200:
                            city = False
                            city2 = False
                            if "name" in result.keys():
                                city = result['name']
                            if not city:
                                if rec.method == 'address':
                                    city = rec.city
                            if rec.method == 'address':
                                    city2 = rec.city

                            temp = pytemperature.k2c(result['main']['temp'])
                            min_temp = pytemperature.k2c(result['main']['temp_min'])
                            max_temp = pytemperature.k2c(result['main']['temp_max'])
                            weather_rec = self.search([('user_id', '=', rec.user_id.id)])
                            now_utc = datetime.now(timezone('UTC'))
                            user_list = self.env['res.users'].search([('id', '=', user_id)])
                            if user_list.partner_id.tz:
                                tz = pytz.timezone(user_list.partner_id.tz)
                                now_pacific = now_utc.astimezone(timezone(str(tz)))
                                current_time = now_pacific.strftime('%d %B %Y, %I:%M%p')
                                vals = {
                                    'date_weather_update': current_time,
                                    'name': city,
                                    'city': city2,
                                    'user_id': user_id,
                                    'weather': result['weather'][0]['main'],
                                    'description': result['weather'][0]['description'],
                                    'temp': temp,
                                    'pressure': result['main']['pressure'],
                                    'humidity': result['main']['humidity'],
                                    'min_temp': min_temp,
                                    'max_temp': max_temp,
                                }
                                if weather_rec:
                                    weather_rec.write(vals)
                                    return {
                                        'issue': ''
                                    }
                                else:
                                    weather_rec.create(vals)
                                    return {
                                        'issue': ''
                                    }
                            else:
                                return {
                                    'issue': 'timezone'
                                }
                        else:
                            return {
                                'issue': 'localization'
                            }
                else:
                    return {
                        'issue': 'bad_request'
                    }
            else:
                return {
                    'issue': 'internet'
                }
        else:
            return {
                'issue': 'config'
            }


class UserWeatherMapConfig(models.Model):
    _name = 'user.weather.map.config'
    _inherit = 'res.config.settings'
    _rec_name = 'user_id'

    def _default_street(self):
        rec = self.search([('user_id', '=', self.env.user.id)])
        if rec:
            return rec.street

    def _default_city(self):
        rec = self.search([('user_id', '=', self.env.user.id)])
        if rec:
            return rec.city

    def _default_state_id(self):
        rec = self.search([('user_id', '=', self.env.user.id)])
        if rec:
            return rec.state_id.id

    def _default_country_id(self):
        rec = self.search([('user_id', '=', self.env.user.id)])
        if rec:
            return rec.country_id.id

    def _default_zip(self):
        rec = self.search([('user_id', '=', self.env.user.id)])
        if rec:
            return rec.zip

    def _default_appid(self):
        rec = self.search([('user_id', '=', self.env.user.id)])
        if rec:
            return rec.appid

    def _default_method(self):
        rec = self.search([('user_id', '=', self.env.user.id)])
        if rec:
            return rec.method
        else:
            return 'address'

    def _default_longitude(self):
        rec = self.search([('user_id', '=', self.env.user.id)])
        if rec:
            if rec.method == 'coordinates':
                return rec.u_longitude
            else:
                return ''

    def _default_latitude(self):
        rec = self.search([('user_id', '=', self.env.user.id)])
        if rec:
            if rec.method == 'coordinates':
                return rec.u_latitude
            else:
                return ''

    user_id = fields.Many2one('res.users', string='User Name', readonly=True, default=lambda self: self.env.user.id)
    u_longitude = fields.Char(string='Longitude', default=_default_longitude)
    u_latitude = fields.Char(string='Latitude', default=_default_latitude)

    street = fields.Char('Street', default=_default_street)
    zip = fields.Char('Zip', size=24, change_default=True, default=_default_zip)
    city = fields.Char('City', default=_default_city)
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', default=_default_state_id)
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', default=_default_country_id)
    appid = fields.Char('App id', default=_default_appid, required=True,
                        help="Just sign up the OpenWeatherMap. Generate a Weather Key and provide here.")
    method = fields.Selection([('address', 'By Address'),
                               ('coordinates', 'By geolocation')], string='Type', default=_default_method)

    @api.multi
    def onchange_state(self, state_id):
        if state_id:
            state = self.env['res.country.state'].browse(state_id)
            return {'value': {'country_id': state.country_id.id}}
        return {}


    @api.multi
    def execute_weather(self):
        val = 0
        recs = self.search([('user_id', '=', self.user_id.id)])
        for rec1 in recs:
            if val < rec1.id:
                val = rec1.id
        for rec2 in recs:
            if val != rec2.id:
                rec2.unlink()
        if self.method == 'address':
            self.geo_localize()
        else:
            pass
        self.env['user.weather.map'].get_weather(self.user_id.id)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web',
            'target': 'self',
        }

    def geo_query_address(self, street=None, zip=None, city=None, state=None, country=None):
        if country and ',' in country and (country.endswith(' of') or country.endswith(' of the')):
            # put country qualifier in front, otherwise GMap gives wrong results,
            # e.g. 'Congo, Democratic Republic of the' => 'Democratic Republic of the Congo'
            country = '{1} {0}'.format(*country.split(',', 1))
        return tools.ustr(', '.join(filter(None, [street,
                                                  ("%s %s" % (zip or '', city or '')).strip(),
                                                  state,
                                                  country])))

    def geo_find(self, addr):
        url = 'https://maps.googleapis.com/maps/api/geocode/json?sensor=false&address='
        url += urllib.quote(addr.encode('utf8'))
        try:
            result = json.load(urllib.urlopen(url))
        except Exception, e:
            raise odoo.exceptions.except_orm(_('Network error'),
                                 _('Cannot contact geolocation servers. '
                                   'Please make sure that your internet connection is up and running (%s).') % e)
        if result['status'] != 'OK':
            return None

        try:
            geo = result['results'][0]['geometry']['location']
            return float(geo['lat']), float(geo['lng'])
        except (KeyError, ValueError):
            return None

    @api.one
    def geo_localize(self):
        # Don't pass context to browse()! We need country names in english below
        result = self.geo_find(self.geo_query_address(street=self.street,
                                                      zip=self.zip,
                                                      city=self.city,
                                                      state=self.state_id.name,
                                                      country=self.country_id.name))
        if result:
            self.write({
                           'u_latitude': result[0],
                           'u_longitude': result[1],
                       }, )
        else:
            if self.method == 'address':
                self.write({
                    'u_latitude': '',
                    'u_longitude': '',
                }, )
        return True
