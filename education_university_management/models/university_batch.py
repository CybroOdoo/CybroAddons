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


class UniversityBatch(models.Model):
    """For managing batches of every department in the university"""
    _name = 'university.batch'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "University Batches"

    @api.model_create_multi
    def create(self, vals):
        """Return the name as a str of semester + academic year"""
        for val in vals:
            if 'semester_id' in val or 'academic_year_id' in val :
                semester_id = self.env['university.semester'].browse(
                    val['semester_id'])
                academic_year_id = self.env['university.academic.year'].browse(
                    val['academic_year_id'])
                if semester_id and academic_year_id:
                    name = f"{semester_id.name} - {academic_year_id.name}"
                    val['name'] = name
        return super(UniversityBatch, self).create(vals)

    name = fields.Char(string="Name", help="Name of the Batch", readonly=True)
    semester_id = fields.Many2one('university.semester',
                                  string="Semester", required=True,
                                  help="Select the semester")
    department_id = fields.Many2one(related='semester_id.department_id',
                                    string="Department",
                                    help="In which department this "
                                         "batch belongs to")
    academic_year_id = fields.Many2one('university.academic.year',
                                       string="Academic Year", required=True,
                                       help="Select the academic year")
    batch_strength = fields.Integer(string='Batch Strength',
                                    help="Total strength of the batch")
    faculty_id = fields.Many2one('university.faculty',
                                 string='Faculty', help="Batch tutor/Faculty")
    batch_student_ids = fields.One2many('university.student',
                                        'batch_id',
                                        string="Students",
                                        help="Students of this Batch")
