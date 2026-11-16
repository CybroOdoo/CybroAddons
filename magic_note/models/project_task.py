# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models


class ProjectTask(models.Model):
    """ Inherits the class to add new fields deadline and note_color in notes
    Methods:
        _compute_note_color():
            Computes the colors for notes based on configured intervals
    """
    _inherit = 'project.task'

    note_color = fields.Char(
        string='Color',
        compute='_compute_note_color',
        help='Color of note'
    )

    @api.depends('date_deadline')
    def _compute_note_color(self):
        """
        Computes the color of the note dynamically
        based on configured date intervals.
        """

        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        interval_records = self.env['note.color'].search([])
        today = fields.Date.context_today(self)
        default_color = ir_config_parameter.get_str(
            'magic_note.note_color_default'
        )
        after_deadline_color = ir_config_parameter.get_str(
            'magic_note.after_deadline'
        )
        not_in_interval_color = ir_config_parameter.get_str(
            'magic_note.not_in_interval'
        )
        for note in self:
            if not note.date_deadline:
                note.note_color = default_color
                continue
            deadline_date = fields.Date.to_date(note.date_deadline)
            if not interval_records:
                if today <= deadline_date:
                    note.note_color = default_color
                else:
                    note.note_color = after_deadline_color
            else:
                assigned_color = False
                for interval in interval_records:
                    if not isinstance(interval.start_interval, type(today)):
                        continue
                    if not isinstance(interval.end_interval, type(today)):
                        continue
                    if interval.start_interval <= deadline_date <= interval.end_interval:
                        assigned_color = interval.color_note
                        break
                if assigned_color:
                    note.note_color = assigned_color

                elif today > deadline_date:
                    note.note_color = after_deadline_color

                else:
                    note.note_color = not_in_interval_color
