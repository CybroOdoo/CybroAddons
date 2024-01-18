# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Config settings for selecting destination language"""
    _inherit = 'res.config.settings'

    destination_language = fields.Selection([
        ('am', 'AMHARIC'), ('ar', 'ARABIC'), ('bn', 'BENGALI'),
        ('zh', 'CHINESE'),
        ('en', 'ENGLISH'), ('el', 'GREEK'), ('gu', 'GUJARATI'),
        ('hi', 'HINDI'),
        ('kn', 'KANNADA'), ('ml', 'MALAYALAM'), ('mr', 'MARATHI'),
        ('ne', 'NEPALI'),
        ('or', 'ORIYA'), ('fa', 'PERSIAN'), ('pa', 'PUNJABI'),
        ('ru', 'RUSSIAN'),
        ('sa', 'SANSKRIT'), ('sr', 'SERBIAN'), ('si', 'SINHALESE'),
        ('ta', 'TAMIL'),
        ('te', 'TELUGU'), ('ti', 'TIGRINYA'), ('ur', 'URDU')],
        string='Language', default='ml',
        config_parameter='transliterate_widget.destination_language',
        help='Choose A Language')
