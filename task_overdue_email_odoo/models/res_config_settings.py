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
    """This is an Odoo model for system configuration settings related to overdue
    task notifications. It inherits from the 'res.config.settings' model and adds
    boolean and integer fields for configuring overdue task notifications."""

    _inherit = "res.config.settings"

    is_notification = fields.Boolean(
        string="Overdue Notification",
        config_parameter="task_overdue_email_odoo.is_notification",
        help="Enable email notifications for overdue project tasks.",
    )
    overdue_days = fields.Integer(
        string="Overdue Days",
        config_parameter="task_overdue_email_odoo.overdue_days",
        help="Number of days after the due date before a notification is sent.",
    )
