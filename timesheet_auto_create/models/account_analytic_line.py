# -*- coding: utf-8 -*-
###############################################################################
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
        project_rec = self.env['project.project'].sudo().create({'name': project})
        return project_rec

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """ Overrides mail_thread message_new that is called by the mail gateway
            through message_process. This override updates the document
            according to the email.
            The work sheet must contain sl.no, project, task, hours spent(float)
            and remark. """
        email_address_list = email_split(msg_dict.get('email_from', ''))
        email_address = email_address_list[0] if email_address_list else False
        employee = False
        if email_address:
            employee = self.env['hr.employee'].sudo().search(
                ['|', ('work_email', 'ilike', email_address),
                 ('user_id.email', 'ilike', email_address)], limit=1)
        if not employee and msg_dict.get('author_id'):
            author_partner = self.env['res.partner'].sudo().browse(msg_dict['author_id'])
            if author_partner.user_ids:
                employee = self.env['hr.employee'].sudo().search(
                    [('user_id', 'in', author_partner.user_ids.ids)], limit=1)

        if not employee:
            return self.env['account.analytic.line']

        company = employee.company_id or (employee.user_id.company_id if employee.user_id else self.env.company)

        html_body = BeautifulSoup(msg_dict.get('body') or '', "lxml")
        tables = html_body.find_all("table")
        head = ['No', 'project_id', 'task_id', 'status', 'unit_amount', 'name']

        timesheets = self.env['account.analytic.line']

        for table in tables:
            rows = table.find_all("tr")
            if not rows:
                continue

            header_cells = [cell.get_text().strip().lower() for cell in rows[0].find_all(["th", "td"])]
            if not any('project' in h for h in header_cells):
                continue

            for row in rows[1:]:
                tds = [td.get_text().strip() for td in row.find_all("td")]
                if len(tds) < 6:
                    continue

                rec = dict(zip(head, tds))
                proj_name = str(rec.get('project_id') or '').strip()
                task_name = str(rec.get('task_id') or '').strip()

                if not proj_name or not task_name:
                    continue

                if proj_name.lower() in ['project', 'project_id'] or task_name.lower() in ['name', 'task', 'task_id']:
                    continue

                project_id = self.env['project.project'].sudo().search(
                    [('name', '=', proj_name)], limit=1)
                if not project_id:
                    project_id = self._create_project(proj_name, task_name)

                task_id = self.env['project.task'].sudo().search(
                    [('name', '=', task_name),
                     ('project_id', '=', project_id.id)], limit=1)
                if not task_id:
                    task_id = self.env['project.task'].sudo().create({
                        'name': task_name,
                        'project_id': project_id.id
                    })

                status = 'completed' if rec.get('status', '').strip().lower() == 'completed' else 'ongoing'

                try:
                    unit_amount = float(rec.get('unit_amount', 0))
                except (ValueError, TypeError):
                    unit_amount = 0.0

                vals = {'name': str(rec.get('name') or '/'),
                        'unit_amount': unit_amount,
                        'project_id': project_id.id,
                        'task_id': task_id.id,
                        'status': status,
                        'employee_id': employee.id,
                        'company_id': company.id}

                if custom_values:
                    vals.update(custom_values)

                timesheet = self.env['account.analytic.line'].sudo().with_company(company).create(vals)
                timesheets |= timesheet

        if not timesheets:
            return self.env['account.analytic.line']

        return timesheets[0]
