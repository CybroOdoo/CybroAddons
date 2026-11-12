# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    """ Inherits sale.order.line to add the functions for checking the
    visibility of the pricelists in order lines and applying the pricelists
    to order lines. """
    _inherit = 'sale.order.line'

    pricelist_visibility = fields.Boolean(
        compute="_compute_pricelist_visibility", string="Pricelist Visible",
        help="Multi Pricelist enabled or not")
    applied_pricelist_id = fields.Many2one(
        'product.pricelist',
        string="PriceList",
        help="Price lists that is applied to the order line.")

    @api.depends('applied_pricelist_id')
    def _compute_pricelist_item_id(self):
        super()._compute_pricelist_item_id()
        for line in self:
            if line.applied_pricelist_id and line.product_id and not line.display_type:
                order_date = line._get_order_date() if hasattr(line, '_get_order_date') else line.order_id.date_order
                line.pricelist_item_id = line.applied_pricelist_id._get_product_rule(
                    line.product_id,
                    quantity=line.product_uom_qty or 1.0,
                    uom=line.product_uom,
                    date=order_date,
                )

    def _get_pricelist_price(self):
        """ Overriding the _get_pricelist_price method to apply multiple
        pricelists """
        self.ensure_one()
        self.product_id.ensure_one()
        if self.applied_pricelist_id:
            order_date = self._get_order_date() if hasattr(self, '_get_order_date') else self.order_id.date_order
            return self.applied_pricelist_id._get_product_price(
                product=self.product_id.with_context(**self._get_product_price_context()),
                quantity=self.product_uom_qty or 1.0,
                currency=self.currency_id,
                uom=self.product_uom,
                date=order_date,
            )
        return super()._get_pricelist_price()

    def apply_pricelist(self):
        """ This function will help to select all the pricelists for a product
        in order line and apply it"""
        self.ensure_one()
        if not self.product_id:
            return False

        pricelists = self.env['product.pricelist'].search([
            '|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)
        ])
        order_date = self._get_order_date() if hasattr(self, '_get_order_date') else self.order_id.date_order
        product = self.product_id.with_context(**self._get_product_price_context())
        quantity = self.product_uom_qty or 1.0
        uom = self.product_uom or self.product_id.uom_id

        wizard_lines = []
        for pricelist in pricelists:
            res = pricelist._compute_price_rule(
                product,
                quantity=quantity,
                currency=self.currency_id,
                uom=uom,
                date=order_date,
            )
            price, rule_id = res.get(product.id, (0.0, False))
            if rule_id:
                wizard_lines.append((0, 0, {
                    'pricelist_id': pricelist.id,
                    'product_id': self.product_id.id,
                    'unit_price': price,
                    'unit_cost': self.product_id.standard_price,
                    'uom_id': uom.id,
                }))

        if wizard_lines:
            pricelist_wizard = self.env['pricelist.product'].create({
                'order_line_id': self.id,
                'line_ids': wizard_lines,
            })
            return {
                'type': 'ir.actions.act_window',
                'target': 'new',
                'name': _('Select Pricelist'),
                'view_mode': 'form',
                'view_id': self.env.ref(
                    "multi_pricelist.pricelist_wizard_view_form", False).id,
                'res_model': 'pricelist.product',
                'res_id': pricelist_wizard.id,
            }
        else:
            raise UserError(_(
                "No price list is configured for this product!"))

    @api.depends('product_id', 'order_id.state')
    def _compute_pricelist_visibility(self):
        """ Computes pricelist_visibility by checking the config parameter,
        order state, and whether the product variant has any applicable pricelists. """
        is_multi_pricelist = bool(self.env[
            'ir.config_parameter'].sudo().get_param(
            'multi_pricelist.multi_pricelist'))
        for rec in self:
            if not is_multi_pricelist or rec.order_id.state in ['sale', 'done', 'cancel'] or not rec.product_id:
                rec.pricelist_visibility = False
                continue

            pricelists = self.env['product.pricelist'].search([
                '|', ('company_id', '=', False), ('company_id', '=', rec.company_id.id)
            ])
            order_date = rec._get_order_date() if hasattr(rec, '_get_order_date') else rec.order_id.date_order
            quantity = rec.product_uom_qty or 1.0
            uom = rec.product_uom or rec.product_id.uom_id
            product = rec.product_id.with_context(**rec._get_product_price_context())

            has_applicable_pricelist = False
            for pricelist in pricelists:
                rule_id = pricelist._get_product_rule(
                    product,
                    quantity=quantity,
                    uom=uom,
                    date=order_date,
                )
                if rule_id:
                    has_applicable_pricelist = True
                    break

            rec.pricelist_visibility = has_applicable_pricelist

    def unit_price(self, price):
        """ Compute the unit price of the product according to the
        price_list_item. """
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
        elif price.compute_price == 'formula' and price.base == 'pricelist' and price.base_pricelist_id:
            order_date = self._get_order_date() if hasattr(self, '_get_order_date') else self.order_id.date_order
            base_price = price.base_pricelist_id._get_product_price(
                product=self.product_id.with_context(**self._get_product_price_context()),
                quantity=self.product_uom_qty or 1.0,
                currency=self.currency_id,
                uom=self.product_uom,
                date=order_date,
            )
            unt_price = (base_price * (
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
