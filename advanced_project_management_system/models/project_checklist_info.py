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
from odoo import fields, models


class ProjectChecklistInfo(models.Model):
    """ Project checklist details"""
    _name = "project.checklist.info"
    _description = "Project checklist information"

    checklist_id = fields.Many2one('project.checklist',
                                   string='Name',
                                   help="Project checklist details")
    description = fields.Char(string='Description',
                              related='checklist_id.description',
                              help="description about the checklist")
    project_id = fields.Many2one('project.project', string="Project",
                                 help="details of the project")
    date = fields.Date(string='Date', default=fields.Date.today(),
                       help="get the date ")
    state = fields.Selection(
        selection=[('new', 'New'), ('progres', 'In Progress'),
                   ('done', 'Done'), ('cancel', 'Cancel')], default='new',
        readonly=False, string="Status",
        help="Get information about the state")

    def action_set_checklist_complete(self):
        """ Mark the checklist progress and completion"""
        if self.state in ['new', 'progres']:
            self.state = 'done'
            self.project_id.checklist_progress += 100 / float(
                len(self.search([('project_id', '=', self.project_id.id)])))

    def action_set_checklist_close(self):
        """ Checklist cancel details"""
        self.state = 'cancel'
