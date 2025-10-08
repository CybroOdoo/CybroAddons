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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ProjectTaskChecklistInfo(models.Model):
    """ Task checklist details"""
    _name = "project.task.checklist.info"
    _description = "Task checklist information"

    checklist_id = fields.Many2one('project.task.checklist',
                                   string='Name', help="checklist")
    description = fields.Char(string='Description',
                              related='checklist_id.description',
                              help="Description of the checklist info ")
    task_id = fields.Many2one('project.task', string="Task",
                              help="Task details")
    checklist_progress = fields.Integer(string="progress",
                                        help="For tracking the checklist "
                                             "progress and completion")
    date = fields.Date(string='Date', default=fields.Date.today(),
                       help="Get the date information")
    state = fields.Selection(
        selection=[('new', 'New'), ('progres', 'In Progress'),
                   ('done', 'Done'), ('cancel', 'Cancel')], default='new',
        string="Status", help="get the status of the checklist ")

    def action_set_checklist_complete(self):
        """ Managing the checklist progress and completion"""
        if self.state in ['new', 'progres']:
            checklist_template_id = self.env[
                'project.task.checklist.template'].search(
                [('id', 'in', self.task_id.checklist_template_ids.ids)])
            if len(checklist_template_id.checklist_ids.ids) > 0:
                self.task_id.checklist_progress += 100 / float(
                    len(checklist_template_id.checklist_ids.ids))
                self.state = 'done'
            else:
                raise ValidationError(_("Please add checklist"))

    def action_set_checklist_close(self):
        """ Checklist cancel info """
        self.state = 'cancel'
