# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models


class LaundryOrderLine(models.Model):
    """
    Inherits laundry.order.line to add washing type and tax computation
    logic for POS-integrated laundry orders.
    """
    _inherit = 'laundry.order.line'

    # washing_type field is updated with the module Laundry Management
    washing_type = fields.Many2one('washing.type',
                                   string='Washing Type', required=False,
                                   help='The many2one field for relating'
                                        ' to the washing type')
    tax_ids = fields.Many2many('account.tax', string='Taxes',
                               help='The many2one field for relating to '
                                    'the account tax')
    price_tax = fields.Float(compute='_compute_price_tax', string='Total Tax',
                             help='The compute field for calculating price '
                                  'tax')

    @api.depends('qty', 'washing_type_id', 'extra_work_ids', 'tax_ids')
    def _compute_price_tax(self):
        """
        Compute the amounts of the LaundryOrder line ie used to calculate
        subtotal amount with the quantity of product and the washing types.
        """
        for line in self:
            price = line.washing_type_id.amount
            taxes = line.tax_ids.compute_all(price,
                                             line.laundry_id.currency_id,
                                             line.qty,
                                             product=line.product_id,
                                             partner=line.laundry_id.partner_shipping_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
            })
