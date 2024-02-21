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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """
       Model representing the configuration settings for project tasks.
       This class extends the 'res.config.settings' model and provides additional
       functionality related to project task configuration settings.
       """
    _inherit = 'res.config.settings'
    is_email = fields.Boolean(string="Send Email",
                              config_parameter='all_in_one_announcements.is_email',
                              help="Enable to send the work report through e-mail")

    def email_send(self):
        """
        Send email notifications based on configured settings. This method
        retrieves tasks, purchase orders, sale orders, and CRM leads based
        on their respective stages. It generates URLs for each record and
        sends an email notification to the configured recipients
        """
        base_url = self.env['ir.config_parameter'].get_param(
            'web.base.url')
        group_users = self.env['res.groups'].browse(self.env.ref(
            'all_in_one_announcements.announcement_group_manager').id)
        mail = self.env['ir.config_parameter'].sudo()
        task_rec = self.env['project.task'].search(
            [('stage_id.name', '=', 'In Progress')])
        tasks = []
        is_manager = self.env.user in group_users.users
        for rec in task_rec:
            tasks.append({
                'name': rec.name,
                'url': base_url + "/web#active_id=" + str(
                    rec.id) + "&cids=1&id=" + str(
                    rec.id) + "&model=project.task&menu_id="
            })
        purchase_rec = self.env['purchase.order'].search(
            [('state', '=', 'purchase')])
        purchase_order = []
        for rec in purchase_rec:
            purchase_order.append({
                'name': rec.name,
                'url': base_url + "/web#active_id=" + str(
                    rec.id) + "&cids=1&id=" + str(
                    rec.id) + "&model=purchase.order&menu_id="
            })
        sale_order = self.env['sale.order'].search(
            [('state', '=', 'sale')])
        sale_orders = []
        for rec in sale_order:
            sale_orders.append({
                'name': rec.name,
                'url': base_url + "/web#active_id=" + str(
                    rec.id) + "&cids=1&id=" + str(
                    rec.id) + "&model=sale.order&menu_id="
            })
        crm_lead = self.env['crm.lead'].search([('stage_id.name', '=', 'Won')])
        crm_leads = []
        for rec in crm_lead:
            crm_leads.append({
                'name': rec.name,
                'url': base_url + "/web#active_id=" + str(
                    rec.id) + "&cids=1&id=" + str(
                    rec.id) + "&model=crm.lead&menu_id="
            })

        if mail.get_param('all_in_one_announcements.is_email'):
            email_values = {
                'email_to': ','.join(group_users.users.mapped('login')),
            }
            mail_template = self.env.ref(
                'all_in_one_announcements.announcement_email_template').sudo()
            mail_template.with_context(
                {'is_manager': is_manager, 'tasks': tasks,
                 'purchase_orders': purchase_order, 'sale_order': sale_orders,
                 'crm_lead': crm_leads}).send_mail(self.id, force_send=True,
                                                   email_values=email_values)
