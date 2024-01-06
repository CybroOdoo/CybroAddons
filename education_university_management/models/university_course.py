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


class UniversityCourse(models.Model):
    """Used to managing the courses of university"""
    _name = 'university.course'
    _description = "University Courses"

    name = fields.Char(string="Name", required=True, help="Name of the course")
    category = fields.Selection(
        [('ug', 'Under Graduation'), ('pg', 'Post Graduation'),
         ('diploma', 'Diploma')], string="Course Category", required=True,
        help="In which category the course belong")
    no_semester = fields.Integer(string="No.of Semester",
                                 help="No.of semesters in each course")
