# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Raveena V (odoo@cybrosys.com)
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

    def _get_display_price(self, product):
        """Overwrite the function to set the unit price according to the
        applied pricelist from the orderline and the UoM"""
        # TO DO: move me in master/saas-16 on sale.order
        # awa: don't know if it's still the case since we need the
        # "product_no_variant_attribute_value_ids" field now
        # to be able to compute the full price
        # it is possible that a no_variant attribute is still in a variant if
        # the type of the attribute has been changed after creation.
        no_variant_attributes_price_extra = [
            ptav.price_extra for ptav in
            self.product_no_variant_attribute_value_ids.filtered(
                lambda ptav:
                ptav.price_extra and
                ptav not in product.product_template_attribute_value_ids
            )
        ]
        if no_variant_attributes_price_extra:
            product = product.with_context(
                no_variant_attributes_price_extra=tuple(
                    no_variant_attributes_price_extra)
            )
        if self.order_id.pricelist_id.discount_policy == 'with_discount':
            if self.applied_pricelist_id:
                return product.with_context(
                    pricelist=self.applied_pricelist_id.id, uom=self.product_uom.id,
                    quantity=self.product_uom_qty
                    ).price
            else:
                return product.with_context(
                    pricelist=self.order_id.pricelist_id.id,
                    uom=self.product_uom.id).price
        product_context = dict(self.env.context,
                               partner_id=self.order_id.partner_id.id,
                               date=self.order_id.date_order,
                               uom=self.product_uom.id)
        final_price, rule_id = self.order_id.pricelist_id.with_context(
            product_context).get_product_price_rule(product or self.product_id,
                                                    self.product_uom_qty or 1.0,
                                                    self.order_id.partner_id)
        base_price, currency = self.with_context(
            product_context)._get_real_price_currency(product, rule_id,
                                                      self.product_uom_qty,
                                                      self.product_uom,
                                                      self.order_id.pricelist_id.id)
        if currency != self.order_id.pricelist_id.currency_id:
            base_price = currency._convert(
                base_price, self.order_id.pricelist_id.currency_id,
                self.order_id.company_id or self.env.company,
                self.order_id.date_order or fields.Date.today())
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

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
                pricelist_wizard = self.env['pricelist.wizard'].create({
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
            'res_model': 'pricelist.wizard',
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
