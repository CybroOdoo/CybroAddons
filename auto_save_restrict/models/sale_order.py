from odoo import models, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """ Confirm the given quotation(s) and set their confirmation date.

        If the corresponding setting is enabled, also locks the Sale Order.

        :return: True
        :rtype: bool
        :raise: UserError if trying to confirm cancelled SO's
        """

        # Filter out orders that are already confirmed or don't need confirmation
        orders_to_confirm = self.env['sale.order']
        for order in self:
            error_msg = order._confirmation_error_message()
            if error_msg:
                if order.state in ('sale', 'done', 'cancel'):
                    continue
                raise UserError(error_msg)
            orders_to_confirm |= order

        # If no orders to confirm, return early
        if not orders_to_confirm:
            return True

        orders_to_confirm.order_line._validate_analytic_distribution()

        for order in orders_to_confirm:
            # ensure the record exists in DB before checking followers
            if not order.id:
                order.flush()

            # Refresh follower cache
            order.invalidate_recordset(['message_partner_ids'])

            # Check if already followed directly in DB
            self.env.cr.execute("""
                SELECT 1 FROM mail_followers
                WHERE res_model = %s AND res_id = %s AND partner_id = %s
                LIMIT 1
            """, ('sale.order', order.id, order.partner_id.id))
            already_follower = self.env.cr.fetchone()

            if not already_follower:
                try:
                    with self.env.cr.savepoint():
                        order.message_subscribe([order.partner_id.id])
                except Exception:
                    pass  # partner already subscribed (race condition, etc.)

        orders_to_confirm.write(
            orders_to_confirm._prepare_confirmation_values()
        )

        # Remove unwanted context
        context = self._context.copy()
        context.pop('default_name', None)

        orders_to_confirm.with_context(context)._action_confirm()

        user = orders_to_confirm[:1].create_uid
        if user and user.sudo().has_group('sale.group_auto_done_setting'):
            orders_to_confirm.action_lock()

        if self.env.context.get('send_email'):
            orders_to_confirm._send_order_confirmation_mail()

        return True
