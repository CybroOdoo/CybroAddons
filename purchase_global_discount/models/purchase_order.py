# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Safa KB(<https://www.cybrosys.com>)
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
from odoo import models, fields, api



class PurchaseOrder(models.Model):
    """inherited purchase to add fields for global discount """
    _inherit = 'purchase.order'

    global_discount = fields.Float(string='Discount', help='To add global discount')

    @api.depends('order_line.price_total', 'global_discount')
    def _amount_all(self):
        """Apply global discount on the computed sale order total."""
        res = super()._amount_all()
        for rec in self:
            if rec.global_discount:
                discount_amount = rec.amount_total * (rec.global_discount / 100)
                rec.amount_total -= discount_amount
        return res

    def _prepare_invoice(self):
        """Pass global discount value from sale order to the generated invoice."""
        res = super()._prepare_invoice()
        for rec in self:
            res['global_discount'] = rec.global_discount if rec.global_discount else 0
        return res
