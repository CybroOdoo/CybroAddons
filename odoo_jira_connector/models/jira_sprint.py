# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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


class JiraSprint(models.Model):
    """Represents a Jira sprint within Odoo."""
    _name = "jira.sprint"
    _description = "jira sprint"

    sprint_id_jira = fields.Integer(string="Sprint id", readonly=True,
                                    help="sprint id in jira.")
    name = fields.Char(string="Sprint Name", help="Name of the sprint.")
    sprint_goal = fields.Text(string="Goal", help="Goal of the sprint.")
    start_date = fields.Datetime(string="Start Date", help="Sprint start date.")
    end_date = fields.Datetime(string="End Date", help="Sprint end date.")
    project_id = fields.Many2one('project.project', readonly=True,
                                 help="Respective Project ID.")
    state = fields.Selection(string="State",
                             selection=[('to_start', 'To start'),
                                        ('ongoing', 'Ongoing'),
                                        ('completed', 'Completed')],
                             default='to_start', help="State of the sprint.")

    def action_get_tasks(self):
        """Returns an action to view tasks currently in the sprint."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tasks',
            'view_mode': 'kanban',
            'res_model': 'project.task',
            'views': [[False, 'kanban'], [False, 'tree'], [False, 'form']],
            'domain': [('project_id', '=', self.project_id.id),
                       ('sprint_id.state', '=', 'ongoing')],
            'context': "{'create': False}"
        }

    def action_get_backlogs(self):
        """Returns an action to view tasks in the sprint's backlog."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Backlogs',
            'view_mode': 'kanban',
            'res_model': 'project.task',
            'views': [[False, 'kanban'], [False, 'tree'], [False, 'form']],
            'domain': [('project_id', '=', self.project_id.id),
                       ('sprint_id.state', '=', 'to_start')],
            'context': "{'create': False}"
        }

    def action_get_all_tasks(self):
        """Returns an action to view all tasks associated with the project."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'All Tasks',
            'view_mode': 'kanban',
            'res_model': 'project.task',
            'views': [[False, 'kanban'], [False, 'tree'], [False, 'form']],
            'domain': [('project_id', '=', self.project_id.id)],
            'context': "{'create': False}"
        }
