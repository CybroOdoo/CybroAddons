# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Syamili K(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """Inherited the model to add new fields for select vendor and
    purchase order."""
    _inherit = "sale.order"

    vendor_id = fields.Many2one('res.partner', string="Vendor",
                                help="Choose vendor for create new purchase "
                                     "order")
    purchase_id = fields.Many2one('purchase.order',
                                  string="Purchase Order",
                                  domain=[('state', '=', 'draft')],
                                  help="Choose a purchase order from the list "
                                       "to add the chosen orders to an "
                                       "existing PO.")

    def action_convert_po(self):
        """Button action for check fields and convert sale order line to
        purchase order line into the new or existing purchase order"""
        if self.env['sale.order.line'].search_count(
                [('order_id', '=', self.id), ('is_check', '=', True)]) >= 1:
            if self.purchase_id:
                purchase = self.purchase_id
            elif self.vendor_id:
                purchase = self.env['purchase.order'].create(
                    {'partner_id': self.vendor_id.id})
            else:
                raise ValidationError(_("Select Vendor or Purchase Order"))
        else:
            raise ValidationError(_("Select Order Line"))
        for rec in self.env['sale.order.line'].search(
                [('order_id', '=', self.id)]):
            if rec.is_check:
                self.env['purchase.order.line'].create({
                    'product_id': rec.product_id.id,
                    'name': rec.name,
                    'product_qty': rec.product_uom_qty,
                    'price_unit': rec.product_id.standard_price,
                    'order_id': purchase.id,
                    'taxes_id': rec.tax_id,
                })
        action = self.env.ref('purchase.action_rfq_form')
        if self.purchase_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': _('Selected Order Lines added to existing '
                                 'Purchase Order. %s',),
                    'links': [{
                        'label': purchase.name,
                        'url': f'#action={action.id}&id={purchase.id}'
                               f'&model=purchase.order'
                    }],
                    'next': {
                        'type': 'ir.actions.act_window_close'
                    },
                }
            }
        elif self.vendor_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': _('New Purchase Order has been placed. %s',),
                    'links': [{
                        'label': purchase.name,
                        'url': f'#action={action.id}&id={purchase.id}'
                               f'&model=purchase.order'
                    }],
                    'next': {
                        'type': 'ir.actions.act_window_close'
                    },
                }
            }


class SaleOrderLine(models.Model):
    """Inherited to add new boolean field in order line."""
    _inherit = "sale.order.line"

    is_check = fields.Boolean(string="Select",
                              help="Check box added for select "
                                   "sale order lines.")
