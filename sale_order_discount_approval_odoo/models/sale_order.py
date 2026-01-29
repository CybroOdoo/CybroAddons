# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shonima(<https://www.cybrosys.com>)
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


class SaleOrderDiscount(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(
        selection_add=[('waiting_for_approval', 'Waiting For Approval'),
                       ('sale',)],
        help="A new state is added when discount limit is exceeded by "
             "salesperson")
    approval_user_id = fields.Many2one('res.users',
                                       string='Discount Approved By',
                                       help='The discount Approver')

    def action_confirm(self):
        """Method for confirming the sale order discount and sending mail for
         the approvar if approval limit crossed"""
        res = super(SaleOrderDiscount, self).action_confirm()
        to_approve = False
        discount_vals = self.order_line.mapped('discount')
        approval_users = self.env.ref(
            'sale_order_discount_approval_odoo.group_approval_manager').users
        user_discount = self.env.user.allow_discount
        if self.env.user.discount_control:
            for rec in discount_vals:
                if rec > user_discount:
                    to_approve = True
                    break
        if to_approve:
            url = str(self.env["ir.config_parameter"].sudo().get_param(
                "web.base.url")) + '/web#' + 'id=' + str(
                self.id) + '&model=' + str(self._name) + '&view_type=form'
            for user in approval_users:
                mail_body = f""""
                <p>Hello,</p>
                       <p>New sale order {self.name} Created with Discount by 
                        {self.env.user.name} 
                       need your approval on it.</p>
                       <p>To Approve, Cancel Order, Click on the Following 
                       Link:
                       <a href='{url}' style="display: inline-block; 
                       padding: 11px; text-decoration: none; font-size: 12px;
                        background-color: #875A7B; color: #fff;
                         border-radius: 5px;"><strong>Click Me</strong></a>
                       </p>
                       <p>Thank You.</p>"""
                mail_values = {
                    'subject': "'%s' Discount Approval Request" % (self.name),
                    'body_html': mail_body,
                    'email_to': user.partner_id.email,
                    'model': 'sale.order',
                }
                template_id = self.env.ref(
                    'sale_order_discount_approval_odoo.confirmation_mail_send'
                ).id
                template = self.env['mail.template'].browse(template_id)
                template.sudo().send_mail(self.id, email_values=mail_values,
                                          force_send=True)
            self.state = 'waiting_for_approval'
        return res

    def action_waiting_approval(self):
        """Method for approving the sale order discount"""
        self.approval_user_id = self.env.user.id
        self.state = 'sale'
