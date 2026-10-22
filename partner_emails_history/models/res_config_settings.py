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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """This is used to add new configuration set up for partner email
    history."""
    _inherit = 'res.config.settings'

    is_history = fields.Boolean(string="Show History",
                                help="If enabled, the history will be shown",
                                config_parameter='partner_emails_history'
                                                 '.default_is_history')
    is_sms_history = fields.Boolean(string="Show SMS History",
                                    help="If enabled, the SMS history will "
                                         "be shown",
                                    config_parameter='partner_emails_history'
                                                     '.default_is_sms_history')
    is_email_history = fields.Boolean(string="Show Email History",
                                      help="If enabled, the email history "
                                           "will be shown",
                                      config_parameter='partner_emails_history'
                                                       '.default_is_email_history')
