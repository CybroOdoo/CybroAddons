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

class MailActivitySchedule(models.TransientModel):
    """Inheriting wizard 'mail.activity.schedule' to add reminder field in wizard and pass it to mail.activity."""
    _inherit = 'mail.activity.schedule'

    reminder_due_date = fields.Date(
        string='Reminder Due Date',
        help='Reminder due date')

    def _action_schedule_activities(self):
        activities = super()._action_schedule_activities()
        if self.reminder_due_date and activities:
            activities.write({'reminder_due_date': self.reminder_due_date})
        return activities

    def _action_schedule_activities_personal(self):
        activity = super()._action_schedule_activities_personal()
        if self.reminder_due_date and activity:
            activity.write({'reminder_due_date': self.reminder_due_date})
        return activity
