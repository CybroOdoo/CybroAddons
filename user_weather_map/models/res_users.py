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
import requests
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    """inherit the res.users model to add custom fields and methods"""
    _inherit = "res.users"

    api_key = fields.Char(string='API Key', help="API key from OpenWeatherMap")
    location_set = fields.Selection(selection=[
        ('auto', 'Use Browser Location'),
        ('manual', 'Manual Location'),
    ], string="Set Location", default='auto',
        help="Use Browser Location:Fetching data based on browsers location,"
             "Manual Location:Need to specify the city in the city field ")
    city = fields.Char(string='City', help="Enter the city")

    @api.constrains('city')
    def _check_city(self):
        """Constraints to check city is valid or not"""
        for rec in self:
            if rec.api_key:
                url = 'https://api.openweathermap.org/data/2.5/weather?q=%s&appid=%s' \
                      % (rec.city, rec.api_key)
                city_check = requests.get(url).json()
                if city_check['cod'] != 200:
                    raise ValidationError(_(city_check['message']))
