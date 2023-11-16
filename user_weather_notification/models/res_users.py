# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu Vijayan KK (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import requests
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    """
    Extends the 'res.users' model to include additional fields related to
    weather information.
    """
    _inherit = "res.users"

    api_key = fields.Char(string='API Key', help="API key from OpenWeatherMap")
    location_set = fields.Selection(selection=[
        ('auto', 'Use Browser Location'),
        ('manual', 'Manual Location'),
    ], string="Set Location", default='auto',
        help="Setting and managing locations")
    city = fields.Char(string='City', help="City of the user")

    @api.constrains('city')
    def _check_city(self):
        """Constraints to check city is valid or not"""
        for rec in self:
            if rec.api_key:
                url = ('https://api.openweathermap.org/data/2.5/weather?q=%s'
                       '&appid=%s') % (
                rec.city, rec.api_key)
                city_check = requests.get(url).json()
                if city_check['cod'] != 200:
                    raise ValidationError(_(city_check['message']))
