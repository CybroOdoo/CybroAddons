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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Transient model for Odoo configuration settings."""
    _inherit = "res.config.settings"

    def _default_mail_icon_id(self):
        """Method to return default mail_icon model
        Returns:
            record:A record of mail_icon"""
        return self.env['mail.icon'].search([], order='id desc', limit=1)

    mail_icon_id = fields.Many2one("mail.icon",
                                   default=_default_mail_icon_id,
                                   ondelete='cascade',
                                   string="Mail Icon Id",
                                   help="Select the mail icon for"
                                        " customization.")
    icon = fields.Binary('Mail Icon',
                         related='mail_icon_id.mail_icon',
                         readonly=False,
                         help="Binary data of the selected mail icon.")
    custom_mail_logo = fields.Boolean(string="Custom Mail Logo",
                                      help="Enable to customize your mail logo",
                                      config_parameter="odoo_mail_management"
                                                       ".custom_mail_logo")
