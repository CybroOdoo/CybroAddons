# -*- coding: utf-8 -*-

from odoo import models, api, fields


class ProjectColor(models.Model):
    _inherit = 'project.project'

    color_name = fields.Char(string='Name')
    project_colors = fields.Many2one('colour.code', string="Colour Code")
    color = fields.Integer(string='Colour')

    @api.onchange('project_colors')
    def _change_color_type(self):
        if self.project_colors:
            self.color = self.project_colors.color
            self.color_name = self.project_colors.name


class Color(models.Model):
    _name = 'colour.code'

    name = fields.Char(string='Name', required=True,
                       help="White : 0,Grey : 1,Pink :2,Yellow :3,Light Green : 4 ,Light Blue :5,"
                            "Sky Blue : 6, Light Orange : 7,Purple: 8,Light Purple: 9")
    color = fields.Integer('Colour Index', required=True, size=1,
                           help="White : 0,Grey : 1,Pink :2,Yellow :3,Light Green : 4 ,Light Blue :5,"
                                "Sky Blue : 6, Light Orange : 7,Purple: 8,Light Purple: 9")


class TaskColor(models.Model):
    _inherit = 'project.task'

    task_color_name = fields.Char(string='Name')
    task_color = fields.Many2one('colour.code', readonly=True, string='Related Colour Code', related="project_id.project_colors")
    color = fields.Integer(string='Colour', related="project_id.color")

    @api.onchange('task_color')
    def _change_task_type(self):
        if self.task_color:
            self.color = self.task_color.color
            self.task_color_name = self.task_color.name





