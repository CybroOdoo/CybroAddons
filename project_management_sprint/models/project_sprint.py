# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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


class ProjectSprint(models.Model):
    """ Sprint in Project """
    _name = 'project.sprint'
    _inherit = 'mail.thread'
    _description = 'Project Sprint'

    name = fields.Char(string="Sprint Name",
                       help="Enter a clear name to identify this sprint.")
    sprint_goal = fields.Html(
        string="Goal",
        help="Describe the objectives or outcomes the team should achieve "
             "during this sprint.")
    start_date = fields.Datetime(
        string="Start Date",
        help="Specify when the sprint is planned to begin.")
    end_date = fields.Datetime(
        string="End Date",
        help="Specify when the sprint is expected to finish.")
    project_id = fields.Many2one('project.project', readonly=True,
                                 help="Project to which this sprint belongs.")
    state = fields.Selection(string="State",
                             selection=[('to_start', 'To start'),
                                        ('ongoing', 'Ongoing'),
                                        ('completed', 'Completed')],
                             default='to_start',
                             help="Current progress status of the sprint.")

    def action_get_tasks(self):
        """ Sprint added tasks """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tasks',
            'view_mode': 'kanban,list,form',
            'res_model': 'project.task',
            'views': [[False, 'kanban'], [False, 'list'], [False, 'form']],
            'domain': [('project_id', '=', self.project_id.id),
                       ('sprint_id', '=', self.id)],
            'context': {'create': False}
        }

    def action_get_backlogs(self):
        """ Tasks without any sprint """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Backlogs',
            'view_mode': 'kanban,list,form',
            'res_model': 'project.task',
            'views': [[False, 'kanban'], [False, 'list'], [False, 'form']],
            'domain': [('project_id', '=', self.project_id.id),
                       ('sprint_id', '=', False)],
            'context': {'create': False}
        }

    def action_get_all_tasks(self):
        """ All tasks in the project """
        return {
            'type': 'ir.actions.act_window',
            'name': 'All Tasks',
            'view_mode': 'kanban,list,form',
            'res_model': 'project.task',
            'views': [[False, 'kanban'], [False, 'list'], [False, 'form']],
            'domain': [('project_id', '=', self.project_id.id)],
            'context': {'create': False}
        }

    def action_start_sprint(self):
        """ Sprint state to ongoing """
        self.write({'state': 'ongoing'})

    def action_finish_sprint(self):
        """ Sprint state to completed """
        self.write({'state': 'completed'})

    def action_reset_states(self):
        """ Sprint state to to_start """
        self.write({'state': 'to_start'})
