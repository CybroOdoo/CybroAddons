# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohamed Muzammil VP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import requests
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    """Inherit the res.users model to add custom fields and methods"""
    _inherit = "res.users"

    api_key = fields.Char(string='API Key', help="API key from OpenWeatherMap")
    location_set = fields.Selection(
        selection=[('auto', 'Use Browser Location'),
                   ('manual', 'Manual Location')],
        string="Set Location", default='auto',
        help="Use Browser Location: Fetching data based on browsers location,"
             "Manual Location:Need to specify the city in the city field")
    city = fields.Char(string='City',
                       help="Enter the city name to find weather")

    @api.constrains('city')
    def _check_city(self):
        """Constraints to check if the city is valid or not"""
        try:
            for rec in self:
                if rec.api_key:
                    url = f'https://api.openweathermap.org/data/2.5/weather?q={rec.city}&appid={rec.api_key}'
                    try:
                        # Set timeout to 5 seconds
                        response = requests.get(url, timeout=5)
                        response_json = response.json()
                        if response_json['cod'] != 200:
                            raise ValidationError(_(response_json['message']))
                    except requests.Timeout:
                        raise ValidationError(
                            _('API request timed out. Please check your '
                              'internet connection or try again later.'))
        except requests.exceptions.ConnectionError:
            raise ValidationError(
                _('Please check your internet connection or try again later.'))

    @api.constrains('city', 'location_set')
    def validation_of_city(self):
        """The city name should be required if the location is set to
        manual."""
        if self.location_set == 'manual' and self.city is False:
            raise ValidationError(_('Please Enter a city name'))
