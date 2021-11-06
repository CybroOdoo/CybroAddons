# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, tools


class ProjectSubTaskHistory(models.Model):
    _name = "report.project.subtask.user"
    _description = "Sub Tasks by user and project"
    _auto = False

    name = fields.Char(string='Sub Task', readonly=True)
    user_id = fields.Many2one('res.users', string='Assigned To', readonly=True)
    date_start = fields.Datetime(string='Assignation Date', readonly=True)
    no_of_days = fields.Integer(string='# of Days', size=128, readonly=True)
    date_deadline = fields.Date(string='Deadline', readonly=True)
    date_last_stage_update = fields.Datetime(string='Last Stage Update', readonly=True)
    task_id = fields.Many2one('project.task', string='Task', readonly=True)
    closing_days = fields.Float(string='Days to Close', digits=(16, 2), readonly=True, group_operator="avg",
                                help="Number of Days to close the task")
    opening_days = fields.Float(string='Days to Assign', digits=(16, 2), readonly=True, group_operator="avg",
                                help="Number of Days to Open the task")
    delay_endings_days = fields.Float(string='Over passed Deadline', digits=(16, 2), readonly=True)
    nbr = fields.Integer(string='# of Tasks', readonly=True)  # TDE FIXME master: rename into nbr_tasks
    priority = fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High')],
                                string='Priority', size=1, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    stage_id = fields.Many2one('project.sub_task.type', string='Stage')

    _order = 'name desc'

    def _select(self):
        select_str = """
             SELECT
                    (select 1 ) AS nbr,
                    t.id as id,
                    t.date_start as date_start,
                    t.date_deadline as date_deadline,
                    abs((extract('epoch' from (t.write_date-t.date_start)))/(3600*24))  as no_of_days,
                    t.task_ref as task_id,
                    t.assigned_user as user_id,
                    t.date_last_stage_update as date_last_stage_update,
                    t.priority,
                    t.name as name,
                    t.company_id,
                    t.stage_id as stage_id,
                    (extract('epoch' from (t.write_date-t.create_date)))/(3600*24)  as closing_days,
                    (extract('epoch' from (t.date_start-t.create_date)))/(3600*24)  as opening_days,
                    (extract('epoch' from (t.date_deadline-(now() at time zone 'UTC'))))/(3600*24)  as delay_endings_days
        """
        return select_str

    def _group_by(self):
        group_by_str = """
                GROUP BY
                    t.id,
                    create_date,
                    write_date,
                    date_start,
                    date_deadline,
                    date_last_stage_update,
                    t.assigned_user,
                    t.priority,
                    name,
                    t.company_id,
                    stage_id
        """
        return group_by_str

    def init(self):
        tools.sql.drop_view_if_exists(self._cr, 'report_project_subtask_user')
        self._cr.execute("""
            CREATE view report_project_subtask_user as
              %s
              FROM project_sub_task t
                WHERE t.active = 'true'
                %s
        """% (self._select(), self._group_by()))
