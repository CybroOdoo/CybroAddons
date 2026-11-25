#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import _, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """Inherit sale.order to add discount approval workflow and approver."""
    _inherit = 'sale.order'

    state = fields.Selection(
        selection_add=[
            ('waiting_for_approval', 'Waiting For Approval'),
            ('sale',),
        ],
    )
    approval_user_id = fields.Many2one(
        'res.users',
        string='Discount Approved By',
        copy=False,
        readonly=True,
        help='User who approved the discount on this order.',
    )

    def _confirmation_error_message(self):
        """Allow confirmation if order is waiting for approval."""
        self.ensure_one()
        if self.state == 'waiting_for_approval':
            return False
        return super()._confirmation_error_message()

    def action_confirm(self):
        """Confirm sale order with discount approval verification.

        If line-level or global discount exceeds the user's allowed limit,
        hold the order in 'waiting_for_approval', log to chatter, and dispatch
        an email notification to discount approval managers without confirming.
        """
        if self.env.context.get('skip_discount_check'):
            return super().action_confirm()

        orders_to_approve = self.env['sale.order']
        orders_to_confirm = self.env['sale.order']

        group = self.env.ref(
            'sale_order_discount_approval_odoo.'
            'sale_order_discount_approval_odoo_group_manager',
            raise_if_not_found=False,
        )
        approval_users = (
            (group.all_user_ids | group.user_ids)
            if group else self.env['res.users']
        )
        user_discount = self.env.user.allow_discount
        discount_product = self.env.company.sale_discount_product_id

        for order in self:
            # If user has no discount control or order was already approved:
            if not self.env.user.is_discount_control or order.approval_user_id:
                orders_to_confirm |= order
                continue

            to_approve = False

            # 1. Line-based discount check
            for line in order.order_line:
                if line.discount > user_discount:
                    to_approve = True
                    break

            # 2. Global discount check
            if not to_approve and discount_product:
                discount_line = order.order_line.filtered(
                    lambda line: line.product_id == discount_product,
                )
                if discount_line:
                    discount_amount = abs(
                        sum(discount_line.mapped('price_unit')),
                    )
                    base_total = sum(
                        sol.product_uom_qty * sol.price_unit
                        for sol in order.order_line
                        if sol.product_id != discount_product
                        and not sol.display_type
                    )
                    if base_total > 0:
                        global_discount_pct = (
                            discount_amount / base_total
                        ) * 100
                        if global_discount_pct > user_discount:
                            to_approve = True

            if to_approve:
                orders_to_approve |= order
            else:
                orders_to_confirm |= order

        for order in orders_to_approve:
            order.state = 'waiting_for_approval'
            order.message_post(
                body=(
                    f"Order discount exceeds user limit ({user_discount}%). "
                    "Submitted for discount manager approval."
                ),
            )
            order._send_discount_approval_notification(approval_users)

        if orders_to_confirm:
            return super(SaleOrder, orders_to_confirm).action_confirm()

        return True

    def _send_discount_approval_notification(self, approval_users):
        """Send email notifications to discount approval managers."""
        self.ensure_one()
        action = self.env.ref(
            'sale.action_quotations_with_onboarding',
            raise_if_not_found=False,
        )
        action_id = action.id if action else ''
        menu = self.env.ref(
            'sale.menu_sale_quotations',
            raise_if_not_found=False,
        )
        menu_param = f"&menu_id={menu.id}" if menu else ""
        redirect_link = (
            f"/web#id={self.id}&action={action_id}&model=sale.order"
            f"&view_type=form{menu_param}"
        )
        base_url = self.get_base_url()
        url = f"{base_url}{redirect_link}"

        btn_style = (
            'display: inline-block; padding: 10px; text-decoration: none; '
            'font-size: 12px; background-color: #875A7B; color: #fff; '
            'border-radius: 5px;'
        )

        for user in approval_users:
            if not user.partner_id.email:
                continue
            mail_body = (
                f"<p>Hello,</p>"
                f"<p>A new sales order '<strong>{self.name}</strong>' created "
                f"with a discount by <strong>{self.env.user.name}</strong> "
                f"requires your approval.</p>"
                f"<p>To review and approve or cancel the order, please click "
                f"the following link:<br/><br/>"
                f"<a href='{url}' style='{btn_style}'>"
                f"<strong>View Order</strong></a></p>"
                f"<p>Thank you.</p>"
            )
            mail_values = {
                'subject': f"{self.name} - Discount Approval Request",
                'body_html': mail_body,
                'email_to': user.partner_id.email,
                'email_from': (
                    self.env.user.partner_id.email or self.env.company.email
                ),
                'model': 'sale.order',
                'res_id': self.id,
            }
            mail_id = self.env['mail.mail'].sudo().create(mail_values)
            mail_id.send()

    def action_waiting_approval(self):
        """Approve sale order discount, record approver and chatter log."""
        if not self.env.user.has_group(
            'sale_order_discount_approval_odoo.'
            'sale_order_discount_approval_odoo_group_manager',
        ):
            raise UserError(
                _("Only Discount Approval Managers can approve this order."),
            )
        for order in self:
            order.approval_user_id = self.env.user.id
            order.message_post(
                body=f"Discount approved by {self.env.user.name}.",
            )
        return self.with_context(skip_discount_check=True).action_confirm()

    def action_draft(self):
        """Reset order to draft and clear previous approval user."""
        res = super().action_draft()
        self.approval_user_id = False
        return res
