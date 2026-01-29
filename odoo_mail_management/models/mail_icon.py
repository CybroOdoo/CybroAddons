# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Hafeesul Ali(<https://www.cybrosys.com>)
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
#############################################################################
import base64
from odoo import api, fields, models, tools
from odoo.modules.module import get_resource_path


class MailIcon(models.Model):
    """Model representing a mail icon."""
    _name = "mail.icon"
    _description = "Mail Icon"

    def _get_default_logo(self):
        """Method to load default logo
        Returns:
            byte:default logo"""
        img_path = get_resource_path('odoo_mail_management',
                                     'static/src/img/logo.png')
        with tools.file_open(img_path, 'rb') as f:
            return base64.b64encode(f.read())

    mail_icon = fields.Binary(string="Mail Icon", help="Mail Icon",
                              default=_get_default_logo)

    @api.model_create_multi
    def create(self, vals_list):
        """Method to super create function and call _handle_icon() function"""
        for vals in vals_list:
            self._handle_icon(vals)
        mail_settings = super().create(vals_list)
        return mail_settings

    def write(self, values):
        """Method to super write function and call _handle_icon() function"""
        self._handle_icon(values)
        mail_settings = super().create(values)
        return mail_settings

    @api.model
    def _handle_icon(self, vals):
        """Method to handle the icon"""
        if 'mail_icon' in vals:
            vals['mail_icon'] = tools.image_process(vals['mail_icon'],
                                                    size=(256, 256),
                                                    crop='center',
                                                    output_format='ICO')

    @api.model
    def load_logo(self):
        """Method to load logo into mail view
        Returns:
            byte:logo to load in mail view"""
        return self.env['mail.icon'].search([], order="id desc", limit=1). \
            mail_icon
