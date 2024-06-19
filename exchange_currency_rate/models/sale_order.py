# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya Babu (odoo@cybrosys.com)
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
##############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    """This class extends the base 'sale.order' model to introduce a
    new field, 'is_exchange',which allows users to manually apply an exchange
    rate for a transaction. When this option is enabled,users can specify the
    exchange rate through the 'rate' field."""
    _inherit = 'sale.order'

    is_exchange = fields.Boolean(string='Apply Manual Currency',
                                 help='Enable the boolean field to display '
                                      'rate field')
    rate = fields.Float(string='Rate', help='specify the currency rate',
                        compute='_compute_rate', readonly=False, store=True,
                        default=1)

    @api.depends('order_line.product_id')
    def _compute_rate(self):
        """Changing the unit price of product by changing the rate."""
        for rec in self:
            if len(rec.order_line) >= 1 and rec.is_exchange:
                rec.order_line[-1].price_unit = rec.order_line[
                                                    -1].product_id.list_price * rec.rate
