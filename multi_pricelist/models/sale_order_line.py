# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from datetime import datetime
from odoo import fields, models, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    """Inherits Sale order line to add the functions for checking the
    visibility of the pricelists in order lines and also apply the
    pricelist to order lines"""
    _inherit = 'sale.order.line'

    pricelist_visibility = fields.Boolean(
        compute="_compute_pricelist_visibility", string="Pricelist Visible",
        help="Multi Pricelist enabled or not")
    applied_pricelist_id = fields.Many2one('product.pricelist',
                                           string="PriceList",
                                           help="Price lists that is applied to"
                                                "the order line.")

    def _get_pricelist_price(self):
        # Overriding the _get_pricelist_price method to apply multiple pricelist
        self.ensure_one()
        self.product_id.ensure_one()
        if self.applied_pricelist_id:
            for line in self:
                line.pricelist_item_id = line.applied_pricelist_id._get_product_rule(
                    line.product_id,
                    quantity=line.product_uom_qty or 1.0,
                    uom=line.product_uom,
                    date=line.order_id.date_order,
                )
            price = self.pricelist_item_id._compute_price(
                product=self.product_id.with_context(
                    **self._get_product_price_context()),
                quantity=self.product_uom_qty or 1.0,
                uom=self.product_uom,
                date=self.order_id.date_order,
                currency=self.currency_id,
            )
            return price
        else:
            price = self.pricelist_item_id._compute_price(
                product=self.product_id.with_context(
                    **self._get_product_price_context()),
                quantity=self.product_uom_qty or 1.0,
                uom=self.product_uom,
                date=self.order_id.date_order,
                currency=self.currency_id,
            )
            return price

    def apply_pricelist(self):
        """This function will help to select all the pricelists
        for a product in order line and apply it"""
        for rec in self:
            date_time_today = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            # find the matching price list for a product
            price_ids = self.env['product.pricelist.item'].search(
                ['|', '|', ('product_tmpl_id', '=', False),
                 ('categ_id', '=', rec.product_id.categ_id.id),
                 ('product_tmpl_id', '=', rec.product_id.product_tmpl_id.id),
                 ('min_quantity', '<=', rec.product_uom_qty),'|',
                 ('date_start', '<=', date_time_today),
                 ('date_start', '=', False), '|',
                 ('date_end', '>=', date_time_today),
                 ('date_end', '=', False),
                 ])
            variant_ids = self.env['product.pricelist.item'].search(
                [
                    ('product_id', '=', rec.product_id.id),
                    ('min_quantity', '<=', rec.product_uom_qty),
                    '|', ('date_start', '<=', date_time_today),
                    ('date_start', '=', False), '|',
                    ('date_end', '>=', date_time_today),
                    ('date_end', '=', False),
                ])
            combined_ids = price_ids + variant_ids
            if combined_ids:
                pricelist_wizard = self.env['pricelist.product'].create({
                    'order_line_id': rec.id,
                    'line_ids': [(0, 0, {
                        'pricelist_id': price.pricelist_id.id,
                        'product_id': rec.product_id.id,
                        'unit_price': self.unit_price(price),
                        'unit_cost': rec.product_id.standard_price,
                        'uom_id': rec.product_id.uom_id.id
                    }) for price in combined_ids],
                })
            else:
                raise UserError(_(
                    "No price list is configured for this product!"))
        return {
            'type': 'ir.actions.act_window',
            'target': 'new',
            'name': 'Select Pricelist',
            'view_mode': 'form',
            'view_id': self.env.ref(
                "multi_pricelist.pricelist_wizard_view_form", False).id,
            'res_model': 'pricelist.product',
            'res_id': pricelist_wizard.id,
        }

    def _compute_pricelist_visibility(self):
        """ Computes pricelist_visibility by checking the config parameter."""
        for rec in self:
            rec.pricelist_visibility = self.env[
                'ir.config_parameter'].sudo().get_param(
                'multi_pricelist.multi_pricelist')
            if rec.order_id.state in ['sale', 'done', 'cancel']:
                rec.pricelist_visibility = False

    def unit_price(self, price):
        """Compute the unit price of the product according to the
        price_list_item"""
        if price.compute_price == 'fixed':
            unt_price = price.fixed_price
        elif price.compute_price == 'percentage' and price.percent_price != 0:
            unt_price = self.product_id.list_price * (
                    1 - price.percent_price / 100)
        elif price.compute_price == 'formula' and price.base == 'list_price':
            unt_price = (self.product_id.list_price * (
                    1 - price.price_discount / 100) + price.price_surcharge)
            if price.price_min_margin or price.price_max_margin:
                if (unt_price < price.price_min_margin +
                        self.product_id.list_price):
                    unt_price = (price.price_min_margin +
                                 self.product_id.list_price)
                elif (unt_price > price.price_max_margin +
                      self.product_id.list_price):
                    unt_price = (price.price_max_margin +
                                 self.product_id.list_price)
                else:
                    unt_price = unt_price
        elif price.compute_price == 'formula' and price.base == 'standard_price':
            unt_price = (self.product_id.standard_price * (
                    1 - price.price_discount / 100) + price.price_surcharge)
            if price.price_min_margin or price.price_max_margin:
                if (unt_price < price.price_min_margin +
                        self.product_id.list_price):
                    unt_price = (price.price_min_margin +
                                 self.product_id.list_price)
                elif (unt_price > price.price_max_margin +
                      self.product_id.list_price):
                    unt_price = (price.price_max_margin +
                                 self.product_id.list_price)
                else:
                    unt_price = unt_price
        elif price.compute_price == 'formula' and price.base == 'pricelist':
            unt_price = (self.unit_price(price.base_pricelist_id.item_ids) * (
                    1 - price.price_discount / 100) + price.price_surcharge)
            if price.price_min_margin or price.price_max_margin:
                if (unt_price < price.price_min_margin +
                        self.product_id.list_price):
                    unt_price = (price.price_min_margin +
                                 self.product_id.list_price)
                elif (unt_price > price.price_max_margin +
                      self.product_id.list_price):
                    unt_price = (price.price_max_margin +
                                 self.product_id.list_price)
                else:
                    unt_price = unt_price
        else:
            unt_price = self.product_id.list_price
        return unt_price
