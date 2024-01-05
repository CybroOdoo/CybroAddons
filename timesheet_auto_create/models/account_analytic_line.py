# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anagha S (odoo@cybrosys.com)
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
###############################################################################
from bs4 import BeautifulSoup
from odoo import api, fields, models
from odoo.tools import email_split


class AccountAnalyticLine(models.Model):
    """This model inherit Account analytic line, Fetch data from incoming mail
    server and create record according to the content of Mail."""
    _name = 'account.analytic.line'
    _inherit = ['account.analytic.line', 'mail.thread']

    status = fields.Selection(
        [('ongoing', 'Ongoing'), ('completed', 'Completed')],
        string='Status', default='ongoing', help='Status of task')

    def _create_project(self, project, task):
        """If the employee added a new project to the work report,
         create a project.
        :param str project: Name of new project;
        :param str task: Name of new task;
        :return recordset project: The project, as a `project.project` record.
         """
        project = self.project_id.create({'name': project})
        self.task_id.create({'name': task, 'project_id': project.id})
        return project

    @api.model
    def message_new(self, msg_dict, custom_values):
        """ Overrides mail_thread message_new that is called by the mail gateway
            through message_process. This override updates the document
            according to the email.
            The work sheet must contain sl.no, project, task, hours spent(float)
            and remark. """
        email_address = email_split(msg_dict.get('email_from', False))[0]
        employee = self.env['hr.employee'].search(
            ['|', ('work_email', 'ilike', email_address),
             ('user_id.email', 'ilike', email_address)], limit=1)
        company = employee.user_id.company_id if employee.user_id else (
            employee.company_id)
        html_body = BeautifulSoup(msg_dict.get('body'), "lxml")
        table = html_body.find("table")
        head = ['No', 'project_id', 'task_id', 'status', 'unit_amount', 'name']
        datasets = [
            dict(zip(head, (td.get_text() for td in row.find_all("td"))))
            for row in table.find_all("tr")[1:]]
        for rec in datasets:
            # Create timesheet from the information from work report
            project_id = self.project_id.sudo().search(
                [('name', '=', str(rec['project_id']))], limit=1)
            if not project_id:
                project_id = self._create_project(rec['project_id'],
                                                  rec['task_id'])
            task_id = self.task_id.sudo().search(
                [('name', '=', str(rec['task_id'])),
                 ('project_id', '=', project_id.id)], limit=1)
            if not task_id:
                task_id = self.task_id.sudo().create({
                    'name': str(rec['task_id']), 'project_id': project_id.id})
            if not employee:
                return task_id
            status = 'completed' if rec['status'] == 'Completed' else 'ongoing'
            vals = {'employee_id': employee.id,
                    'name': str(rec['name']),
                    'unit_amount': rec['unit_amount'],
                    'project_id': project_id.id,
                    'task_id': task_id.id,
                    'status': status,
                    'company_id': company.id}
            if project_id:
                self.env['account.analytic.line'].create(vals)
        return project_id
