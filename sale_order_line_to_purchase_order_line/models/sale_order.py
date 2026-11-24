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

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """Inherited the model to add new fields for select vendor and
    purchase order."""
    _inherit = "sale.order"

    vendor_id = fields.Many2one('res.partner',
                                help="Choose a vendor to create a new purchase "
                                     "order.")
    purchase_id = fields.Many2one('purchase.order',
                                  string="Purchase Order",
                                  domain=[('state', '=', 'draft')],
                                  help="Choose a draft purchase order from the list "
                                       "to add the selected lines to an "
                                       "existing PO.")

    def action_convert_po(self):
        """Button action for check fields and convert sale order line to
        purchase order line into the new or existing purchase order"""
        selected_lines = self.order_line.filtered(
            lambda line: line.is_check and not line.display_type
        )
        if not selected_lines:
            raise ValidationError(
                _("Please select at least one sale order line to convert.")
            )

        if self.purchase_id:
            purchase = self.purchase_id
        elif self.vendor_id:
            purchase = self.env['purchase.order'].create({
                'partner_id': self.vendor_id.id,
            })
        else:
            raise ValidationError(
                _("Please select a Vendor or an existing Purchase Order to proceed.")
            )

        for rec in selected_lines:
            self.env['purchase.order.line'].create({
                'product_id': rec.product_id.id,
                'name': rec.name,
                'product_qty': rec.product_uom_qty,
                'price_unit': rec.product_id.standard_price,
                'order_id': purchase.id,
                'tax_ids':  [(6, 0, rec.tax_ids.ids)],
            })
        if self.purchase_id:
            message = _(
                'Selected Order Lines added to existing Purchase Order. %s',
                purchase.name
            )
        else:
            message = _(
                'New Purchase Order has been placed. %s',
                purchase.name
            )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': self.env._('Success'),
                'message': message,
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window_close'
                },
            }
        }

class SaleOrderLine(models.Model):
    """Inherited to add new boolean field in order line."""
    _inherit = "sale.order.line"

    is_check = fields.Boolean(string="Select",
                              help="Checkbox added to select "
                                   "sale order lines.")
