# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models, fields


class SaleOrderDiscount(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(
        selection_add=[('waiting_for_approval', 'Waiting For Approval'),
                       ('sale',)])
    approval_user_id = fields.Many2one('res.users',
                                       string='Discount Approved By')

    def action_confirm(self):
        """Method for confirming the sale order discount and sending mail for the approvar if approval limit crossed"""
        res = super(SaleOrderDiscount, self).action_confirm()
        to_approve = False
        discount_vals = self.order_line.mapped('discount')
        approval_users = self.env.ref(
            'sale_order_discount_approval_odoo.group_approval_manager').users
        user_discount = self.env.user.allow_discount
        if self.env.user.discount_control == True:
            for rec in discount_vals:
                if rec > user_discount:
                    to_approve = True
                    break

        if to_approve == True:
            display_id = self.id
            action_id = self.env.ref(
                'sale.action_quotations_with_onboarding').id
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            redirect_link = "/web#id=%s&cids=1&menu_id=178&action=%s" \
                            "&model" \
                            "=sale.order&view_type=form" % (
                                display_id, action_id)
            url = base_url + redirect_link
            for user in approval_users:
                mail_body = """
                <p>Hello,</p>
                       <p>New sale order '%s' Created with Discount by '%s' 
                       need your approval on it.</p>
                       <p>To Approve, Cancel Order, Click on the Following 
                       Link:
                       <a href='%s' style="display: inline-block; 
                       padding: 10px; text-decoration: none; font-size: 12px; background-color: #875A7B; color: #fff; border-radius: 5px;"><strong>Click Me</strong></a>
                       </p>
                       <p>Thank You.</p>""" % (self.name, self.env.user.name,
                                               url)
                mail_values = {
                    'subject': "'%s' Discount Approval Request" % (self.name),
                    'body_html': mail_body,
                    'email_to': user.partner_id.email,
                    'model': 'sale.order',
                }
                mail_id = self.env['mail.mail'].sudo().create(mail_values)
                mail_id.sudo().send()
            self.state = 'waiting_for_approval'
        return res

    def action_waiting_approval(self):
        """Method for approving the sale order discount"""
        self.approval_user_id = self.env.user.id
        self.state = 'sale'
