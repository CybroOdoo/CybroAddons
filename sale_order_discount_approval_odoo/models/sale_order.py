# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(<https://www.cybrosys.com>)
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
from odoo import models, fields


class SaleOrder(models.Model):
    """This is used to inherit 'sale.order' to add new fields and
    functionality"""
    _inherit = 'sale.order'

    state = fields.Selection(
        selection_add=[('waiting_for_approval', 'Waiting For Approval'),
                       ('sale',)])
    approval_user_id = fields.Many2one('res.users',
                                       string='Discount Approved By',
                                       help='The discount approver')

    def action_confirm(self):
        """Method for confirming the sale order discount and sending mail for
        the approver if approval limit crossed"""
        res = super().action_confirm()
        to_approve = False
        discount_vals = self.order_line.mapped('discount')
        approval_users = self.env.ref(
            'sale_order_discount_approval_odoo.sale_order_discount_approval_odoo_group_manager').users
        user_discount = self.env.user.allow_discount
        if self.env.user.is_discount_control == True:
            for rec in discount_vals:
                if rec > user_discount:
                    to_approve = True
                    break
        if to_approve:
            action_id = self.env.ref(
                'sale.action_quotations_with_onboarding').id
            redirect_link = f"/web#id={self.id}&cids=1&menu_id=178&action={action_id}" \
                            "&model=sale.order&view_type=form"
            url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url') + redirect_link
            for user in approval_users:
                mail_body = f"""<p>Hello,</p> <p>New sale order '{self.name}' 
                created with Discount by '{self.env.user.name}' need your approval
                 on it.</p> <p>To Approve, Cancel Order, Click on the Following 
                 Link: <a href='{url}' style="display: inline-block; 
                 padding: 10px; text-decoration: none; font-size: 12px; 
                 background-color: #875A7B; color: #fff; border-radius: 5px;
                 "><strong>Click Me</strong></a> </p> <p>Thank You.</p>"""
                mail_values = {
                    'subject': f"{self.name} Discount Approval Request",
                    'body_html': mail_body,
                    'email_to': user.partner_id.email,
                    'email_from': self.env.user.partner_id.email,
                    'model': 'sale.order',
                }
                mail_id = self.env['mail.mail'].sudo().create(mail_values)
                mail_id.send()
            self.state = 'waiting_for_approval'
        return res

    def action_waiting_approval(self):
        """Method for approving the sale order discount"""
        self.approval_user_id = self.env.user.id
        self.state = 'sale'
