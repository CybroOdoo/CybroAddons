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
from odoo import api, fields, models


class PersonalOrganiser(models.Model):
    """This class is used to deal with tasks"""
    _name = "personal.organiser"
    _description = "Personal Organiser"

    user_id = fields.Many2one('res.users', default=lambda self: self.env.user,
                              help="Owner of the task")
    task_title = fields.Char(required=True, string="Title", help="For title")
    date = fields.Datetime(required=True, help="Date field")
    calendar_event_id = fields.Many2one('calendar.event', ondelete='set null',
                                        help="All-day calendar event that "
                                             "shows this task in the calendar")

    def _get_calendar_event_vals(self):
        """Values of the all-day calendar event mirroring this task."""
        self.ensure_one()
        day = fields.Date.to_date(self.date)
        return {
            'name': self.task_title,
            'allday': True,
            'start_date': day,
            'stop_date': day,
            'user_id': self.user_id.id or self.env.uid,
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Create each task's own calendar event alongside it."""
        tasks = super().create(vals_list)
        for task in tasks.filtered(lambda t: not t.calendar_event_id):
            task.calendar_event_id = self.env['calendar.event'].create(
                task._get_calendar_event_vals())
        return tasks

    def write(self, vals):
        """Keep the linked calendar event in step with the task."""
        res = super().write(vals)
        if {'task_title', 'date'} & set(vals):
            for task in self:
                if task.calendar_event_id:
                    task.calendar_event_id.write(task._get_calendar_event_vals())
                else:
                    task.calendar_event_id = self.env['calendar.event'].create(
                        task._get_calendar_event_vals())
        return res

    def unlink(self):
        """Remove the tasks' own calendar events, and only those."""
        events = self.calendar_event_id
        res = super().unlink()
        events.exists().unlink()
        return res

