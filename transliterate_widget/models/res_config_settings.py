# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
###################################################################################

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Config settings for selecting destination language"""
    _inherit = 'res.config.settings'

    destination_language = fields.Selection([
        ('am', 'AMHARIC'), ('ar', 'ARABIC'), ('bn', 'BENGALI'), ('zh', 'CHINESE'),
        ('en', 'ENGLISH'), ('el', 'GREEK'), ('gu', 'GUJARATI'), ('hi', 'HINDI'),
        ('kn', 'KANNADA'), ('ml', 'MALAYALAM'), ('mr', 'MARATHI'), ('ne', 'NEPALI'),
        ('or', 'ORIYA'), ('fa', 'PERSIAN'), ('pa', 'PUNJABI'), ('ru', 'RUSSIAN'),
        ('sa', 'SANSKRIT'), ('sr', 'SERBIAN'), ('si', 'SINHALESE'), ('ta', 'TAMIL'),
        ('te', 'TELUGU'), ('ti', 'TIGRINYA'), ('ur', 'URDU')],
        string='Language', default='ml', config_parameter='transliterate_widget.dest_lang')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            destination_language=self.env['ir.config_parameter'].sudo().get_param('destination_language') or 'en'
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("destination_language", self.destination_language)

    @api.model
    def get_config_value(self, config_name):
        """Method to get config value for rpc call"""
        config_value = self.env['ir.config_parameter'].sudo().get_param(config_name)
        return config_value

