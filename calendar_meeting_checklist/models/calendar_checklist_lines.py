# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class CalendarChecklistLines(models.Model):
    """ This class is used to store checklist items associated with calendar
    events. Each checklist item can be marked as complete or canceled,
    allowing users to track tasks or actions related to specific calendar
    events."""
    _name = 'calendar.checklist.lines'
    _description = 'Checklists lines'
    _order = "sequence asc"

    event_id = fields.Many2one(comodel_name='calendar.event',
                               required=True, ondelete='cascade',
                               copy=False, index=True,
                               help='Each record in this model can be linked '
                                    'to a single calendar event record.')
    sequence = fields.Integer(help='Used to order checklists.')
    checklist_id = fields.Many2one(comodel_name='meeting.checklist',
                                   help='Checklist for the calendar event.')
    stage = fields.Selection(
        selection=[('new', 'New'), ('completed', 'Completed'),
                   ('canceled', 'Canceled')], default='new',
        readonly=True, help='State of checklist.')

    @api.model_create_multi
    def create(self, vals_list):
        """Only users who may edit the event may add lines to it."""
        lines = super().create(vals_list)
        lines.event_id.check_access('write')
        return lines

    def write(self, vals):
        """Only users who may edit the event may change its lines."""
        self.event_id.check_access('write')
        res = super().write(vals)
        if 'event_id' in vals:
            self.event_id.check_access('write')
        return res

    def unlink(self):
        """Only users who may edit the event may remove its lines."""
        self.event_id.check_access('write')
        return super().unlink()

    def action_complete(self):
        """Set the checklist's status to 'completed'."""
        self.stage = 'completed'

    def action_cancel(self):
        """Set the checklist's status to 'canceled'."""
        self.stage = 'canceled'
