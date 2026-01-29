# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, api


class PurchaseLines(models.Model):
    _inherit = 'purchase.order.line'

    discount = fields.Float(string="Discount (%)", editable=True)
    _sql_constraints = [
        (
            "maximum_discount",
            "CHECK (discount <= 100.0)",
            "Discount must be lower than 100%.",
        )
    ]

    @api.depends("discount")
    def _compute_amount(self):
        return super()._compute_amount()

    def _prepare_compute_all_values(self):
        vals = super()._prepare_compute_all_values()
        vals.update({"price_unit": self._get_discounted_price()})
        return vals

    @api.onchange('product_id')
    def calculate_discount_percentage(self):
        vendor = self.order_id.partner_id
        for product in self:
            sellers = product.product_id.product_tmpl_id.seller_ids
            for rec in sellers:
                if rec.name == vendor:
                    if rec.discount:
                        product.write({'discount': rec.discount})
                        product.update({'price_unit': rec.price})
                        break;
                    else:
                        if rec.name.default_discount:
                            product.update({'discount': rec.name.default_discount})
                        break;

                else:
                    self.write({'discount': None})

    @api.depends('discount')
    def _get_discounted_price(self):
        self.ensure_one()
        if self.discount:
            return self.price_unit * (1 - self.discount / 100)
        return self.price_unit

    def _prepare_account_move_line(self, move=False):
        sup = super(PurchaseLines, self)._prepare_account_move_line(move=False)
        sup.update({'discount': self.discount})
        return sup


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.onchange('partner_id')
    def _recompute_discount(self):
        self.order_line.calculate_discount_percentage()
