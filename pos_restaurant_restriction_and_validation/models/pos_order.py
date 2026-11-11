# -*- coding: utf-8 -*-
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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, models
from odoo.exceptions import UserError


class PosOrder(models.Model):
    """Inherits pos.order to enforce manager validation on kitchen orders."""
    _inherit = 'pos.order'

    @api.ondelete(at_uninstall=False)
    def _unlink_except_kitchen_sent(self):
        """Prevents deletion of orders sent to the kitchen without manager approval."""
        for order in self:
            config = order.config_id
            if config.pos_restaurant_restriction and config.pos_order_delete:
                has_kitchen_lines = (
                    bool(order.prep_order_ids)
                    or any(line.prep_line_ids for line in order.lines)
                )
                if has_kitchen_lines:
                    order_ref = order.pos_reference or order.name or order.tracking_number or False
                    if not config.is_restriction_authorized('delete_order', order_ref=order_ref):
                        raise UserError(self.env._(
                            "Manager approval is required to delete an order sent to the kitchen."
                        ))

    def cancel_order_from_pos(self):
        """Prevents cancellation of kitchen orders from POS without manager approval."""
        orders = self
        if not orders and self.env.context.get('active_ids'):
            orders = self.browse(self.env.context.get('active_ids'))
        for order in orders:
            config = order.config_id
            if config.pos_restaurant_restriction and config.pos_order_delete:
                has_kitchen_lines = (
                    bool(order.prep_order_ids)
                    or any(line.prep_line_ids for line in order.lines)
                )
                if has_kitchen_lines:
                    order_ref = order.pos_reference or order.name or order.tracking_number or False
                    if not config.is_restriction_authorized('delete_order', order_ref=order_ref):
                        raise UserError(self.env._(
                            "Manager approval is required to cancel an order sent to the kitchen."
                        ))
        return super().cancel_order_from_pos()

