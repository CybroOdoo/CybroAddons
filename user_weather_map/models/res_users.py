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

import requests
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    """
    Extends the 'res.users' model to include additional fields related to
    weather information.
    """
    _inherit = "res.users"

    api_key = fields.Char(string='API Key', groups='base.group_system',
                          help="API key from OpenWeatherMap")
    location_set = fields.Selection(selection=[
        ('auto', 'Use Browser Location'),
        ('manual', 'Manual Location'),
    ], string="Set Location", default='auto',
        help="Setting and managing locations")
    city = fields.Char(help="City of the user")

    @staticmethod
    def _weather_clean_vals(vals):
        """Drop the spaces or line breaks a pasted API key or city often
        carries; OpenWeatherMap rejects such a key as invalid (401)."""
        for field in ('api_key', 'city'):
            if isinstance(vals.get(field), str):
                vals[field] = vals[field].strip()
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._weather_clean_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        return super().write(self._weather_clean_vals(vals))

    @api.constrains('city', 'api_key', 'location_set')
    def _check_city(self):
        """Checking the city or API key validity"""
        for rec in self:
            if rec.api_key:
                if rec.location_set == 'manual':
                    if not rec.city:
                        raise ValidationError(self.env._(
                            "Please specify a city when 'Manual Location' is selected."))
                    params = {'q': rec.city, 'appid': rec.api_key}
                else:
                    # Default test query for 'auto' browser location to validate the API key
                    params = {'q': 'London', 'appid': rec.api_key}
                try:
                    city_check = requests.get(
                        'https://api.openweathermap.org/data/2.5/weather',
                        params=params, timeout=10).json()
                    cod = str(city_check.get('cod'))
                    if cod != '200':
                        # OpenWeatherMap's own message, shown as sent.
                        raise ValidationError(str(city_check.get('message') or self.env._(
                            'Invalid OpenWeatherMap API key or city.')))
                except requests.exceptions.RequestException as e:
                    raise ValidationError(self.env._(
                        "Could not connect to OpenWeatherMap: %s", str(e))) from e
