# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anagha S (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class CalendarEvent(models.Model):
    """Calendar event inherited model"""
    _inherit = 'calendar.event'

    checklist_template_ids = fields.Many2many(
        'checklist.template', string='Checklist Template',
        help="Select one or more checklist templates to associate with this "
             "record.")
    checklist_line_ids = fields.One2many(
        comodel_name='calendar.checklist.lines', inverse_name='event_id',
        string='Checklists', copy=True, auto_delete=True,
        help='Checklists for calendar event.')
    checklist_progress = fields.Integer(compute='_compute_checklist_progress',
                                        help='Progress of checklist.')
    completed_checklist = fields.Boolean(default=False,
                                         string='Completed all checklists',
                                         help='True when all checklists are'
                                              'completed.')

    def _compute_checklist_progress(self):
        """ Calculates the completion progress of a checklist associated with a
        calendar event. It counts the number of checklist items associated with
        the event and the number of completed checklist items. The progress is
        calculated as a percentage based on the ratio of completed items to
        total items."""
        for rec in self:
            count = rec.checklist_line_ids.search_count(
                [('event_id', '=', rec.id)])
            completed = rec.checklist_line_ids.search_count(
                [('event_id', '=', rec.id), ('stage', '=', 'completed')])
            rec.checklist_progress = (completed / count) * 100 if count != 0 \
                else 0
            rec.completed_checklist = rec.checklist_progress == 100

    @api.onchange('checklist_template_ids')
    def _onchange_checklist_template_ids(self):
        """This method is triggered when the `checklist_template_ids` field is
        modified. It automatically generates checklist lines for the current
        record based on the selected checklist templates."""
        checklist_line_data = [fields.Command.clear()]
        checklist_line_data += [
            fields.Command.create({'checklist_id': line.id, 'stage': 'new'})
            for line in self.checklist_template_ids.checklist_ids]
        self.checklist_line_ids = checklist_line_data
