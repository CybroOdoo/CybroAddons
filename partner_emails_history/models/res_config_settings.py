# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (odoo@cybrosys.com)
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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """This is used to add new configuration set up for partner email
    history."""
    _inherit = 'res.config.settings'

    is_history = fields.Boolean(string="Show history",
                                help="If enabled, it will Show History",
                                config_parameter='partner_emails_history'
                                                 '.default_is_history')
    is_sms_history = fields.Boolean(string="Show Sms history",
                                    help="If enabled it will Show sms history",
                                    config_parameter='partner_emails_history'
                                                     '.default_is_sms_history')
    is_email_history = fields.Boolean(string="Show Email history",
                                      help="If enabled, it will Show "
                                           "email history",
                                      config_parameter='partner_emails_history'
                                                       '.default_is_email_history')

    @api.onchange('is_sms_history', 'is_email_history')
    def _onchange_show_history(self):
        """This is used to add values to the partner form"""
        for rec in self.env['res.partner'].search([]):
            rec.is_show_sms = self.is_sms_history
            rec.is_show_emails = self.is_email_history
