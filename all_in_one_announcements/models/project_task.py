# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models


class ProjectTask(models.Model):
    """
    Model representing a project task.
    This class extends the 'project.task' model and adds additional functionality
    specific to project tasks.
    """
    _inherit = 'project.task'
    is_announcement_send = fields.Boolean(string="Send Email",
                                          help="Enable to send announcement through email")

    @api.model
    def task_assigned(self):
        """
        Get assigned tasks and send announcements if not already sent. This
        method retrieves assigned tasks that are in the 'In Progress' stage,
        and sends announcements to the assigned users if the
        'is_announcement_send' field is False. It also updates the
        'is_announcement_send' field to True after sending the announcements.
        return: A list of dictionaries representing the assigned tasks and
        related objects.
        """
        tasks = self.search([('stage_id.name', '=', 'In Progress')])
        purchase_orders = self.env['purchase.order'].search(
            [('state', '=', 'purchase')])
        sale_orders = self.env['sale.order'].search(
            [('state', '=', 'sale')])
        crm_lead = self.env['crm.lead'].search([('stage_id.name', '=', 'Won')])
        context = {}
        result = []
        mail = self.env['ir.config_parameter'].sudo()
        for task in tasks:
            name = task.project_id.name
            if name in context:
                context[name]['count'] += 1
            else:
                context[name] = {'id': task.project_id.id, 'name': name,
                                 'count': 1, 'model': 'project.task'}
            if not task.is_announcement_send:
                if mail.get_param('all_in_one_announcements.email'):
                    mail_content = "  Hello  " + task.name + "Your Pending " \
                                                             "Task. Please " \
                                                             "Check with the " \
                                                             "Task"
                    main_content = {
                        'email_from': self.env.user.work_email,
                        'email_to': 'demomail1050@gmail.com',
                        'body_html': mail_content,
                        'subject': 'Work Report'
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()
                task.is_announcement_send = True
        task_results = [
            {'id': item['id'], 'name': item['name'], 'model': 'project.task',
             'count': '-' if item['count'] == 1 else item['count']} for item in
            context.values()]
        result.append(task_results)
        purchase_order_results = [{'purchase_order_name': po.name, 'id': po.id,
                                   'model': 'purchase.order', 'count': 1}
                                  for po in purchase_orders]
        result.append(purchase_order_results)
        sale_order_results = [{'sale_order_name': so.name, 'id': so.id,
                               'model': 'sale.order', 'count': 1}
                              for so in sale_orders]
        crm_results = [{'crm_name': rec.name, 'id': rec.id,
                        'model': 'crm.lead', 'count': 1}
                       for rec in crm_lead]
        result.append(sale_order_results)
        result.append(crm_results)
        return result

    @api.model
    def get_pending_tasks(self, project_id):
        """
        Retrieve tasks for a specific project. This method fetches tasks
        related to a particular project ID that are in the 'In Progress'
        stage. It returns an action to open the tasks with the appropriate
        view mode.
        param project_id: The ID of the project to filter tasks by.
        return: A dictionary representing an action to open the project tasks.
        """
        task_ids = self.search([('project_id.id', '=', int(project_id)),
                                ('stage_id.name', '=', 'In Progress')])
        return {
            'name': task_ids[0].project_id.name,
            'type': "ir.actions.act_window",
            'res_model': 'project.task',
            'domain': [('id', 'in', task_ids.ids)],
            'view_mode': "kanban,list,form",
            'context': {'no_breadcrumbs': True},
            'views': [[False, "kanban"]],
            'target': 'main',
        }
