# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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

    def _get_display_price(self):
        """Overwrite the function to set the unit price according to the
        applied pricelist from the orderline and the UoM"""
        if not self.applied_pricelist_id:
            return super()._get_display_price()

        self.ensure_one()
        pricelist_price = self._get_pricelist_price()

        if self.applied_pricelist_id.discount_policy == 'with_discount':
            return pricelist_price

        base_price = self._get_pricelist_price_before_discount()
        return max(base_price, pricelist_price)

    def _get_pricelist_price(self):
        """Compute the price given by the applied pricelist or default pricelist."""
        if not self.applied_pricelist_id:
            return super()._get_pricelist_price()

        self.ensure_one()
        self.product_id.ensure_one()
        order_date = self.order_id.date_order or fields.Date.today()
        product = self.product_id.with_context(**self._get_product_price_context())
        qty = self.product_uom_qty or 1.0
        uom = self.product_uom or self.product_id.uom_id
        currency = self.currency_id or self.order_id.company_id.currency_id

        return self.applied_pricelist_id._get_product_price(
            product, qty, uom, date=order_date, currency=currency)

    def apply_pricelist(self):
        """This function will help to select all the pricelists
        for a product in order line and apply it"""
        for rec in self:
            date_today = fields.Date.today()
            price_items = self.env['product.pricelist.item'].search([
                '|', ('product_id', '=', rec.product_id.id),
                '|', ('product_tmpl_id', '=', rec.product_id.product_tmpl_id.id),
                '|', ('categ_id', '=', rec.product_id.categ_id.id),
                ('applied_on', '=', '3_global'),
                ('min_quantity', '<=', rec.product_uom_qty),
                '|', ('date_start', '<=', date_today), ('date_start', '=', False),
                '|', ('date_end', '>=', date_today), ('date_end', '=', False),
            ])
            pricelists = price_items.mapped('pricelist_id')
            if not pricelists:
                pricelists = self.env['product.pricelist'].search([])

            if pricelists:
                pricelist_wizard = self.env['pricelist.wizard'].create({
                    'order_line_id': rec.id,
                    'line_ids': [(0, 0, {
                        'pricelist_id': price.id,
                        'product_id': rec.product_id.id,
                        'unit_price': price._get_product_price(
                            rec.product_id, rec.product_uom_qty or 1.0, rec.product_uom or rec.product_id.uom_id
                        ),
                        'unit_cost': rec.product_id.standard_price,
                        'uom_id': rec.product_uom.id or rec.product_id.uom_id.id
                    }) for price in pricelists],
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
        param_val = self.env['ir.config_parameter'].sudo().get_param(
            'multi_pricelist.multi_pricelist')
        is_enabled = bool(param_val) and str(param_val).lower() in ['true', '1']
        for rec in self:
            rec.pricelist_visibility = is_enabled and (rec.order_id.state not in ['sale', 'done', 'cancel'])

    def unit_price(self, price):
        """Compute the unit price of the product according to the price list item or pricelist"""
        if hasattr(price, '_get_product_price'):
            return price._get_product_price(
                self.product_id, self.product_uom_qty or 1.0, self.product_uom or self.product_id.uom_id)
        if hasattr(price, 'pricelist_id') and price.pricelist_id:
            return price.pricelist_id._get_product_price(
                self.product_id, self.product_uom_qty or 1.0, self.product_uom or self.product_id.uom_id)
        return self.product_id.list_price
