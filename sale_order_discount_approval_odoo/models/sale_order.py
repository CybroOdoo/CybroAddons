# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
        """Confirm sale order with discount approval check.
           - If line/global discount exceeds user limit → set 'waiting_for_approval'
           - Else → proceed normally.
        """
        self.ensure_one()
        res = super().action_confirm()

        to_approve = False
        user_discount = self.env.user.allow_discount
        discount_product = self.env.company.sale_discount_product_id
        approval_users = self.env.ref(
            'sale_order_discount_approval_odoo.sale_order_discount_approval_odoo_group_manager').users

        # -------------------------------
        # 1. Line-based discount check
        # -------------------------------
        if self.env.user.is_discount_control:
            for line in self.order_line:
                if line.discount > user_discount:
                    to_approve = True
                    break

        # -------------------------------
        # 2. Global discount check
        # -------------------------------
        if not to_approve and discount_product:
            discount_line = self.order_line.filtered(lambda l: l.product_id == discount_product)
            if discount_line:
                discount_amount = abs(discount_line.price_unit)
                # base total before discount
                base_total = sum(
                    l.product_uom_qty * l.price_unit for l in self.order_line if l.product_id != discount_product)
                if base_total > 0:
                    global_discount_pct = (discount_amount / base_total) * 100
                    if global_discount_pct > user_discount:
                        to_approve = True

        # -------------------------------
        # 3. Apply result
        # -------------------------------
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
