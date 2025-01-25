# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (Contact : odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models


class ProjectPhase(models.Model):
    """New model for create project phases in project module."""
    _name = 'project.phase'
    _description = "Project Phase"

    name = fields.Char(string="Name", required=True,
                       help="Provide name for record.")
    project_id = fields.Many2one('project.project', string="Project",
                                 help="Choose projects from existing records.")
    start_date = fields.Date(string="Start date", help="Select start date")
    responsible_user_id = fields.Many2one('res.users',
                                          string='Responsible User',
                                          required=True,
                                          help="It's a mandatory field, so "
                                               "please select any user from "
                                               "the list.")
    sequence = fields.Integer(string="Sequence", help="Give a sequence number.")
    end_date = fields.Date(string="End date", help="Select end date.")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 help="By default, current login company will "
                                      "selected here. You can choose other "
                                      "companies also.")
    internal_notes = fields.Html(string="Internal Note",
                                 help="Add internal notes")

    def get_project_tasks(self):
        """A smart tab added in the model, when open the smart tab it will
        redirect to tasks where project phase is equal to the current project
        phase."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tasks',
            'view_mode': 'list,form',
            'res_model': 'project.task',
            'domain': [('project_phase_id', '=', self.name)],
        }

    def open_project_task(self):
        """Function for open tasks related to the project phase in the
        kanban view."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tasks',
            'view_mode': 'list,form',
            'res_model': 'project.task',
            'domain': [('project_phase_id', '=', self.name)],
        }
