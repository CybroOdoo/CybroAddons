# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class ClassLesson(models.Model):
    """Class is used to represent the lessons."""
    _name = 'class.lesson'
    _description = 'Class Lesson'

    name = fields.Char(string='Name', help='Name of the lesson.')
    hours = fields.Char(string='Hours', help='Hours of the lesson.')
    teacher_id = fields.Many2one('hr.employee', string='Teacher',
                                 domain=[('teacher', '=', True)],
                                 help='Teacher assigned to the lesson.')


class ClassLessonType(models.Model):
    """Class is used to represent the lessons."""
    _name = 'class.lesson.type'
    _description = 'Class Lesson Type'

    lesson_id = fields.Many2one('class.lesson',
                                String='Lessons', help='Choose already '
                                                       'created lessons')
    hours = fields.Char(string='Hours',
                        help='Hours of the lesson.')
    teacher_id = fields.Many2one('hr.employee', string='Teacher',
                                 domain=[('teacher', '=', True)],
                                 help='Teacher assigned to the lesson.')
    relation_id = fields.Many2one('class.type',
                                  string='Relation ID',
                                  help='Relation to the corresponding class.')

    @api.onchange('lesson_id')
    def _onchange_lesson_id(self):
        """Change values according to the lesson chosen"""
        if self.lesson_id:
            self.hours = self.lesson_id.hours
            self.teacher_id = self.lesson_id.teacher_id.id
