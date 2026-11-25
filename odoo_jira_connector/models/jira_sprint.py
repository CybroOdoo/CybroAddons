# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class JiraSprint(models.Model):
    """Represents a Jira sprint within Odoo."""
    _name = 'jira.sprint'
    _description = 'Jira Sprint'

    sprint_id_jira = fields.Integer(string='Jira Sprint ID', readonly=True,
                                    help='ID of the sprint in Jira.')
    name = fields.Char(string='Sprint Name', help='Name of the sprint.')
    sprint_goal = fields.Text(string='Goal', help='Goal of the sprint.')
    start_date = fields.Datetime(help='Start date of the sprint.')
    end_date = fields.Datetime(help='End date of the sprint.')
    project_id = fields.Many2one('project.project', readonly=True,
                                 help='Project the sprint belongs to.')
    state = fields.Selection(selection=[('to_start', 'To Start'),
                                        ('ongoing', 'Ongoing'),
                                        ('completed', 'Completed')],
                             default='to_start', help='State of the sprint.')

    def _task_action(self, name, domain):
        """Return a window action showing the project tasks matching ``domain``."""
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'view_mode': 'kanban,list,form',
            'res_model': 'project.task',
            'views': [[False, 'kanban'], [False, 'list'], [False, 'form']],
            'domain': [('project_id', '=', self.project_id.id)] + domain,
            'context': {'create': False},
        }

    def action_get_tasks(self):
        """Returns an action to view tasks currently in the sprint."""
        return self._task_action(self.env._('Tasks'),
                                 [('sprint_id.state', '=', 'ongoing')])

    def action_get_backlogs(self):
        """Returns an action to view tasks in the sprint's backlog."""
        return self._task_action(self.env._('Backlogs'),
                                 [('sprint_id.state', '=', 'to_start')])

    def action_get_all_tasks(self):
        """Returns an action to view all tasks associated with the project."""
        return self._task_action(self.env._('All Tasks'), [])
