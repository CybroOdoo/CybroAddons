# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
"""
This module extends Odoo's ResConfigSettings to provide configuration options
for the Meeting Summarizer module, including Open API settings and email options.
"""
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    """
        This class extends the res.config.settings model to add configuration options
        for the Meeting Summarizer module. It allows users to configure:

        - Whether the Open API feature is enabled.
        - The API key to use with the Open API.
        - Whether to automatically send transcription emails.
        - Who should receive the emails (host or all logged-in users).

        All fields are stored as system-wide configuration parameters.
        """
    _inherit = "res.config.settings"

    open_api_value = fields.Boolean(string="Open API Key",
                                    config_parameter="meeting_summarizer.open_api_value" )
    open_api_key = fields.Char(string="Open API Value",
                               config_parameter="meeting_summarizer.open_api_key" )
    auto_mail_send = fields.Boolean(string="Automatically Send Mail",
                                    config_parameter="meeting_summarizer.auto_mail_send")
    select_user = fields.Selection(
        selection=[
            ('host', 'Host'),
            ('all_attendees', 'All Attendees'),
        ], string="Select Recipients", config_parameter="meeting_summarizer.select_user")
