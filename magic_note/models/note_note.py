# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Rahul CK(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class NoteNote(models.Model):
    """Create new fields deadline and note_color in notes"""
    _inherit = 'note.note'

    deadline = fields.Date(string="Deadline", required=True,
                           default=fields.date.today(),
                           help="Specify deadline of note")
    note_color = fields.Char(string="color", help="Color of Note")

    @api.model
    def _fields_view_get(self, view_id=None, view_type='kanban', toolbar=False,
                         submenu=False):
        """
        Check the intervals and set the colors to the notes which is configured
        in settings
        """
        res = super(NoteNote, self)._fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        today_date = fields.date.today()
        for rec in self.search([]):
            days_difference = relativedelta(rec.deadline, today_date).days
            interval_records = self.env['note.color'].search([])
            default_color_config = \
                self.env.ref('magic_note.view_note_configuration')
            if not interval_records:
                if today_date <= rec.deadline:
                    rec.note_color = default_color_config.default_magic_color
                else:
                    rec.note_color = default_color_config.deadline_cross
            else:
                flag = 0
                for interval in interval_records:
                    if interval.start_interval <= days_difference < \
                            interval.end_interval:
                        rec.note_color = interval.color_note
                        flag = 1
                if flag == 0:
                    rec.note_color = default_color_config.not_in_interval
        return res
