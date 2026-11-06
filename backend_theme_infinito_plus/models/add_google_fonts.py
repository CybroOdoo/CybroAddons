# -*- coding: utf-8 -*-
#############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
# Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
# This program is free software: you can modify it under the terms of the
# GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
# You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
# (LGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import re
from urllib.parse import quote_plus

import requests

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

FONT_NAME_RE = re.compile(r'[A-Za-z0-9 ]{1,80}')


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

    name = fields.Char(string='Font Name', required=True,
                       help="Name of the font")
    font_url = fields.Text(string='Font URL', help="Store the font URL")
    font = fields.Text(help="Font style")

    @api.constrains('name')
    def _check_name(self):
        """Allow only letters, digits and spaces in a font name."""
        for font in self:
            if not FONT_NAME_RE.fullmatch(font.name or ''):
                raise ValidationError(self.env._(
                    'A font name can only contain letters, digits and spaces.'))

    @api.model
    def save_google_fonts(self, args):
        """Create a font from its name and page URL and select it.

        Args:
            args (list): The font name and the URL of its page.

        Returns:
            int: The id of the new font.
        """
        if not self.env.user.has_group('base.group_system'):
            raise AccessError(self.env._('Only administrators can add fonts.'))
        font_name, font_url = (args[0] or '').strip(), args[1]
        if not FONT_NAME_RE.fullmatch(font_name):
            raise ValidationError(self.env._(
                'A font name can only contain letters, digits and spaces.'))
        if not font_url or not str(font_url).startswith(
                'https://fonts.google.com/'):
            font_url = 'https://fonts.google.com/specimen/%s' % quote_plus(
                font_name)
        if self.search_count([('name', '=', font_name)]):
            raise ValidationError(self.env._('Font already exists.'))
        rec = self.create({
            'name': font_name,
            'font_url': font_url,
            'font': self.get_css(font_name),
        })
        self.env['ir.config_parameter'].sudo().set_param(
            'backend_theme_infinito_plus.font', str(rec.id))
        return rec.id

    @api.model
    def get_css(self, name):
        """Download the CSS of a Google font.

        Args:
            name (str): The font name.

        Returns:
            str: The CSS text returned by Google Fonts.
        """
        url = 'https://fonts.googleapis.com/css?family=%s&display=swap' % (
            quote_plus(name))
        try:
            response = requests.get(url, timeout=5, headers={
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/101.0.4951.41 Safari/537.36'})
            response.raise_for_status()
        except requests.RequestException as error:
            raise UserError(self.env._(
                'The font could not be downloaded from Google Fonts.')) from error
        return response.text

    @api.model
    def get_active_font_css(self):
        """Return the CSS of the selected font, or an empty string."""
        font_id = self.env['ir.config_parameter'].sudo().get_param(
            'backend_theme_infinito_plus.font')
        if not (font_id and font_id.isdigit() and int(font_id)):
            return ''
        font = self.sudo().browse(int(font_id)).exists()
        if not font:
            return ''
        return (
            "%s\n* { font-family: '%s', sans-serif !important; }\n"
            ".fa { font: normal normal normal 14px/1 FontAwesome !important; }\n"
            ".oi { font-family: 'odoo_ui_icons' !important; }"
        ) % (font.font or '', font.name)