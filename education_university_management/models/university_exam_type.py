# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha M K (odoo@cybrosys.com)
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
from odoo import fields, models


class UniversityExamType(models.Model):
    """For managing type of exams such as internal or semester"""
    _name = 'university.exam.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'University Exam Type'

    name = fields.Char(string='Name', required=True,
                       help="Name of the exam type")
    exam_type = fields.Selection(
        [('internal', 'Internal'), ('sem', 'Semester')],
        string='Exam Type', default='internal',
        help="Select exam type for exams")
    company_id = fields.Many2one(
        'res.company', string='Company', help="Company of the "
                                              "exam type",
        default=lambda self: self.env.company)
