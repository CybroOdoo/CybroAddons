# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sigha CK (odoo@cybrosys.com)
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
###############################################################################
import os

import requests

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class GoogleFont(models.Model):
    """Used for adding google fonts"""
    _name = 'infinito.google.font'
    _description = 'Add Google Fonts'

    name = fields.Char(string='Font Name', help="Name of the font")
    font_url = fields.Text(string='Font URL', help="Store the font URL")
    font = fields.Text(string='Font', help="Font style")

    @api.model
    def save_google_fonts(self, g_font):
        """Function to store fonts in database"""
        record = self.search([('font_url', '=', g_font[1])])
        if record:
            # TODO: Raise warning
            raise ValidationError(_('Font already existing'))
        else:
            font = self.get_css(g_font[0])
            rec = self.create({
                'name': g_font[0],
                'font_url': g_font[1],
                'font': font
            })
            rec.set_css()

    def get_css(self, name):
        """get the css file of selected google font"""
        headers_woff2 = {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko)'
                          'Chrome/101.0.4951.41 Safari/537.36',
        }
        url = f'https://fonts.googleapis.com/css?family={name}&display=swap'
        req = requests.get(url, timeout=5, headers=headers_woff2)
        return req.content

    def set_css(self):
        """open the file write the style in to the css file"""
        working_dir = os.path.dirname(os.path.realpath(__file__))
        working_dir = working_dir.replace('/models', '/static/src/css/font.css')
        # open the file in write mode
        with open(working_dir, 'w') as file:
            style = f"""
            {self.font}
            * {{
                font-family: '{self.name}' !important;
            }}
             .fa {{
               font: normal normal normal 14px/1 FontAwesome !important;}}
            .oi {{
                font-family: 'odoo_ui_icons' !important;}}
            """
            file.write(style)

    @staticmethod
    def remove_fonts():
        """remove the style when changing the font"""
        working_dir = os.path.dirname(os.path.realpath(__file__))
        working_dir = working_dir.replace('/models', '/static/src/css/font.css')
        with open(working_dir, 'w') as file:
            file.write('')
