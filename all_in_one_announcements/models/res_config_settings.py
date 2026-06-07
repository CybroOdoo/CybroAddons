# -*- coding: utf-8 -*-
#############################################################################
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
        Send email notifications based on configured settings.
        """
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        group_manager = self.env.ref('all_in_one_announcements.announcement_group_manager')
        mail_param = self.env['ir.config_parameter'].sudo()
        
        if not mail_param.get_param('all_in_one_announcements.is_email'):
            return

        task_stage = self.env.ref('project.project_stage_1')
        task_recs = self.env['project.project'].search([('stage_id', '=', task_stage)])
        tasks = [{
            'name': rec.name,
            'url': f"{base_url}/web#id={rec.id}&model=project.task&view_type=form"
        } for rec in task_recs]

        purchase_recs = self.env['purchase.order'].search([('state', '=', 'purchase')])
        purchase_orders = [{
            'name': rec.name,
            'url': f"{base_url}/web#id={rec.id}&model=purchase.order&view_type=form"
        } for rec in purchase_recs]

        sale_recs = self.env['sale.order'].search([('state', '=', 'sale')])
        sale_orders = [{
            'name': rec.name,
            'url': f"{base_url}/web#id={rec.id}&model=sale.order&view_type=form"
        } for rec in sale_recs]

        crm_stage = self.env.ref("crm.stage_lead4")
        crm_recs = self.env['crm.lead'].search([('stage_id', '=', crm_stage)])
        crm_leads = [{
            'name': rec.name,
            'url': f"{base_url}/web#id={rec.id}&model=crm.lead&view_type=form"
        } for rec in crm_recs]

        is_manager = group_manager in self.env.user.group_ids
        email_to = ','.join(group_manager.user_ids.mapped('email') or group_manager.user_ids.mapped('login'))
        if email_to:
            mail_template = self.env.ref('all_in_one_announcements.announcement_email_template').sudo()
            mail_template.with_context(
                is_manager=is_manager,
                tasks=tasks,
                purchase_orders=purchase_orders,
                sale_order=sale_orders,
                crm_lead=crm_leads
            ).send_mail(self.id, force_send=True, email_values={'email_to': email_to})
