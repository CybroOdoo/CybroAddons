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
import re

import requests

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

from .utils import get_param, set_param


class GoogleFont(models.Model):
    """Google fonts that can be used as the backend font."""
    _name = 'infinito.google.font'
    _description = 'Add Google Fonts'

    name = fields.Char(string='Font Name', help="Name of the font")
    font_url = fields.Text(string='Font URL', help="Store the font URL")
    font = fields.Text(string='Font', help="Font CSS (@font-face rules)")

    @api.model
    def save_google_fonts(self, args):
        """Download a Google font and make it the active font."""
        if not self.env.user.has_group('base.group_system'):
            raise AccessError(_('Only administrators can add fonts.'))
        font_name, font_url = args[0], args[1]
        if not font_url or font_url == 'undefined':
            font_url = 'https://fonts.google.com/specimen/%s' % (
                font_name.replace(' ', '+'))
        if self.search([('name', '=', font_name)]):
            raise ValidationError(_('Font already existing'))
        rec = self.create({
            'name': font_name,
            'font_url': font_url,
            'font': self.get_css(font_name),
        })
        set_param(self.env, 'backend_theme_infinito_plus.font', rec.id)
        return rec.id

    def get_css(self, name):
        """Download the CSS of a Google font."""
        headers = {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) '
                          'Chrome/101.0.4951.41 Safari/537.36',
        }
        try:
            response = requests.get(
                'https://fonts.googleapis.com/css',
                params={'family': name, 'display': 'swap'},
                timeout=15, headers=headers)
            response.raise_for_status()
        except requests.RequestException as error:
            raise UserError(_(
                "Could not download the font '%(name)s' from Google Fonts. "
                "Check the font name and that the server has internet "
                "access.\n\nDetails: %(error)s",
                name=name, error=error))
        return response.text

    @api.model
    def get_active_font_css(self):
        """Return the CSS of the active font, or '' for the system font."""
        font_id = get_param(self.env, 'backend_theme_infinito_plus.font')
        try:
            font = self.browse(int(font_id)).exists()
        except (TypeError, ValueError):
            return ''
        if not font:
            return ''
        family = re.sub(r"[^\w \-]", '', font.name or '')
        return (
            "%s\nbody, input, select, textarea, button, .btn, "
            ".dropdown-menu { font-family: '%s', sans-serif; }\n"
        ) % (font.font or '', family)