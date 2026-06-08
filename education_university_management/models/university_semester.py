# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R(odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class UniversitySemester(models.Model):
    """Used to manage the semester of department"""
    _name = 'university.semester'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "University Semester"

    name = fields.Char(string="Name", help="Name of the semester",
                       compute="compute_semester_name")
    semester_no = fields.Integer(string="Semester", help="Semester number",
                                 required=True)
    department_id = fields.Many2one('university.department',
                                    string="Department",
                                    required=True,
                                    help="In which department the semester "
                                         "belongs to")
    syllabus_ids = fields.One2many('university.syllabus',
                                   'semester_id',
                                   help="Syllabus of semester",
                                   string="Syllabus")

    @api.depends('semester_no','department_id')
    def compute_semester_name(self):
        """ Updates the name field dynamically based on the
        department code and semester number."""
        for rec in self:
            if rec.department_id and rec.semester_no:
                rec.name = f"{rec.department_id.code}/Sem {rec.semester_no}"
            else:
                rec.name = False
