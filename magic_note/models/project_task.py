# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Busthana Shirin (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class ProjectTask(models.Model):
    """ Inherits the class to add new fields deadline and note_color in notes
    Methods:
        get_view():
            Override this method to add colors to notes
    """
    _inherit = 'project.task'

    deadline = fields.Date(string='Deadline', required=True,
                           default=fields.Date.today(),
                           help='Specify deadline for notes')
    note_color = fields.Char(string='Color', help='Color of note')

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        """
        Overrides ORM get_view() to check the intervals and set the colors to
        the notes which is configured in the settings
        Args:
           view_id (int): id of the view or None
           view_type (str): type of the view to return if view_id is None
           options (dict): boolean options to return additional features:
            - bool mobile: true if the web client is currently using the
            responsive mobile view
        Returns:
            dict: composition of the requested view
        """
        res = super().get_view(view_id, view_type, **options)
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        for note in self.search([]):
            days_difference = relativedelta(
                note.deadline, fields.date.today()).days
            interval_records = self.env['note.color'].search([])
            if not interval_records:
                if fields.Date.today() <= note.deadline:
                    note.note_color = ir_config_parameter.get_param(
                        'magic_note.note_color_default')
                else:
                    note.note_color = ir_config_parameter.get_param(
                        'magic_note.after_deadline')
            else:
                flag = 0
                for interval in interval_records:
                    if interval.start_interval <= days_difference < \
                            interval.end_interval:
                        note.note_color = interval.color_note
                        flag = 1
                if flag == 0:
                    note.note_color = ir_config_parameter.get_param(
                        'magic_note.not_in_interval')
        return res
