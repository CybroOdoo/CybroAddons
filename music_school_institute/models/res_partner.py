# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu K P (<https://www.cybrosys.com>)
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
#
#############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    """Model for adding details about the students in contact module."""
    _inherit = 'res.partner'

    student = fields.Boolean(string='Is Student',
                             help='Used to mark the contact as a student.')
    class_id = fields.Many2one('class.type', string='Joined Class',
                              help='Relation field use to connect the class '
                                   'type to the contact.')
    attendance_count = fields.Integer(String='Attendance Count',
                                      compute='_compute_attendance_count',
                                      help='Attendance count displaying field.')
    student_type = fields.Selection(
        [('part_time', 'Part Time'), ('full_time', 'Full Time')],
        string='Course Mode',
        help='Field used to define the student selected class type.')

    def class_attendance_view(self):
        """Function used to view the student attendance."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'class',
            'view_mode': 'tree',
            'res_model': 'students.attendance',
            'domain': [
                ('student_id', '=', self.id)],
            'context': "{'create': False}"}

    def _compute_attendance_count(self):
        """Function used to count the attendance."""
        for record in self:
            record.attendance_count = self.env[
                'students.attendance'].search_count(
                [('student_id', '=', record.id),
                 ('attendance', '=', 'present')])
