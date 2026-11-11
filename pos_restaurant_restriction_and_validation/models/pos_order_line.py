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


class PosOrderLine(models.Model):
    """Inherits pos.order.line to enforce manager approval on kitchen-sent lines."""
    _inherit = 'pos.order.line'

    @api.ondelete(at_uninstall=False)
    def _unlink_except_kitchen_sent(self):
        """Prevents deletion of kitchen-sent lines without manager approval."""
        for line in self:
            config = line.order_id.config_id
            if not (config.pos_restaurant_restriction and config.pos_orderline_delete):
                continue
            if not line.prep_line_ids:
                continue
            order_ref = line.order_id.pos_reference or line.order_id.name or False
            authorized = config.is_restriction_authorized(
                'orderline_delete',
                order_ref=order_ref,
                product_id=line.product_id.id,
            )
            if not authorized:
                raise UserError(self.env._(
                    "Manager approval is required to delete "
                    "an order line sent to the kitchen."
                ))

    def write(self, vals):
        """Prevents modifying quantity of kitchen-sent lines without manager approval."""
        if 'qty' in vals and not self.env.context.get('pos_restriction_approved'):
            for line in self:
                if vals.get('qty') == line.qty:
                    continue
                config = line.order_id.config_id
                if not (config.pos_restaurant_restriction and config.pos_orderline_quantity_update):
                    continue
                if not line.prep_line_ids:
                    continue
                order_ref = line.order_id.pos_reference or line.order_id.name or False
                authorized = config.is_restriction_authorized(
                    'orderline_quantity_update',
                    order_ref=order_ref,
                    product_id=line.product_id.id,
                )
                if not authorized:
                    raise UserError(self.env._(
                        "Manager approval is required to update "
                        "quantity of an order line sent to the kitchen."
                    ))
        return super().write(vals)
