# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ajmunnisa KP (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    """Inherits the purchase.order.line model to include functions to recompute
    discount, total price etc """
    _inherit = 'purchase.order.line'

    discount = fields.Float(string="Discount (%)", help="Vendor's discount "
                                                        "for the product.")
    _sql_constraints = [
        (
            "maximum_discount",
            "CHECK (discount <= 100.0)",
            "Discount must be lower than 100%.",
        )
    ]

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'discount')
    def _compute_price_subtotal(self):
        """
        Overrides the existing _compute_amount function to recompute the prices
        when discount is changed
        """
        for line in self:
            tax_results = self.env['account.tax']. \
                _compute_taxes([line._convert_to_tax_base_line_dict()])
            totals = list(tax_results['totals'].values())[0]
            amount_untaxed = totals['amount_untaxed']
            amount_tax = totals['amount_tax']
            line.update({
                'price_subtotal': amount_untaxed,
                'price_tax': amount_tax,
                'price_total': amount_untaxed + amount_tax,
            })

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
        Compute the discount percentage when the product is changed
        """
        for line in self:
            for rec in line.product_id.product_tmpl_id.seller_ids:
                if rec.partner_id == self.order_id.partner_id:
                    if rec.discount:
                        line.write({'discount': rec.discount})
                    else:
                        if rec.partner_id.default_discount:
                            line.update(
                                {'discount': rec.partner_id.default_discount})
                else:
                    self.write({'discount': None})

    def _prepare_account_move_line(self, move=False):
        """Method for updating the discount amount in account move line"""
        res = super()._prepare_account_move_line(move=False)
        res.update({'discount': self.discount})
        return res

    def _get_discounted_price(self):
        """
        Compute the price per unit after applying the discount
        """
        self.ensure_one()
        if self.discount:
            return self.price_unit * (1 - self.discount / 100)
        return self.price_unit

    def _convert_to_tax_base_line_dict(self):
        """Overrides the existing _convert_to_tax_base_line_dict method to
        compute the price_unit based on discount. Convert the current record
        to a dictionary in order to use the generic taxes computation method
        defined on account.tax.
        :return: A python dictionary.
        """
        self.ensure_one()
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.order_id.partner_id,
            currency=self.order_id.currency_id,
            product=self.product_id,
            taxes=self.taxes_id,
            price_unit=self._get_discounted_price(),
            quantity=self.product_qty,
            price_subtotal=self.price_subtotal,
        )
