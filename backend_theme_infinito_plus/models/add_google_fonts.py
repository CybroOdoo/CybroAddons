# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import os

import requests

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class GoogleFont(models.Model):
    """Model for adding Google fonts.

    This model is used to store information about Google fonts.

    Attributes:
        _name (str): The technical name of the model.
        _description (str): Description of the model.

    Fields:
        name (Char): Name of the font.
        font_url (Text): URL of the font.
        font (Text): Font style.
    """
    _name = 'infinito.google.font'
    _description = 'Add Google Fonts'

    name = fields.Char(string='Font Name', help="Name of the font")
    font_url = fields.Text(string='Font URL', help="Store the font URL")
    font = fields.Text(string='Font', help="Font style")

    @api.model
    def save_google_fonts(self, args):
        """Save fonts to the database.

        This method saves fonts to the database and generates CSS for the font.

        Args:
            args (list): A list containing the font name and font URL.

        Returns:
            None

        Raises:
            ValidationError: If the font already exists in the database.
        """
        record = self.search([('font_url', '=', args[1])])
        if record:
            # TODO: Raise warning
            raise ValidationError(_('Font already existing'))
        else:
            font = self.get_css(args[0])
            rec = self.create({
                'name': args[0],
                'font_url': args[1],
                'font': font
            })
            self.env['ir.config_parameter'].sudo().set_param('backend_theme_infinito_plus.font',
                      rec.id)
            rec.set_css()

    def get_css(self, name):
        """Get the CSS file of the selected Google font.

        This method retrieves the CSS file of the selected Google font using its name.

        Args:
            name (str): The name of the Google font.

        Returns:
            bytes: The content of the CSS file.

        Raises:
            requests.Timeout: If the request times out.
            requests.RequestException: If there's an issue with the request.
        """
        headers_woff2 = {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko)'
                          'Chrome/101.0.4951.41 Safari/537.36',
        }
        url = f'https://fonts.googleapis.com/css?family={name}&display=swap'
        req = requests.get(url, timeout=5, headers=headers_woff2)
        return req.content

    def set_css(self):
        """Open the CSS file and write the font style.

        This method opens the CSS file and writes the font style into it.

        Returns:
            None

        Raises:
            Any exceptions raised during file operations."""
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
        """Remove the font styles.

        This method removes the font styles by clearing the content of the CSS file.

        Returns:
            None

        Raises:
            Any exceptions raised during file operations."""
        working_dir = os.path.dirname(os.path.realpath(__file__))
        working_dir = working_dir.replace('/models', '/static/src/css/font.css')
        with open(working_dir, 'w') as file:
            file.write('')
