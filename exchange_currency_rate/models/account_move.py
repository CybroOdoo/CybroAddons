# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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


class AccountMove(models.Model):
    """This class extends the base 'purchase.order' model to introduce a new
     field, 'is_exchange',which allows users to manually apply an exchange
     rate for a transaction. When this option is enabled,users can specify
    the exchange rate through the 'rate' field."""
    _inherit = 'account.move'

    is_exchange = fields.Boolean(string='Apply Manual Exchange',
                                 help='Check this box if you want to manually '
                                      'apply an exchange rate for this '
                                      'transaction.')
    rate = fields.Float(string='Rate', help='specify the rate',
                        compute='_compute_rate', readonly=False, store=True,
                        default=1)

    @api.depends('invoice_line_ids.product_id')
    def _compute_rate(self):
        """Changing the unit price of product by changing the rate."""
        for rec in self:
            if rec.move_type == 'out_invoice':
                if len(rec.invoice_line_ids) >= 1 and rec.is_exchange:
                    rec.invoice_line_ids[-1].price_unit = rec.invoice_line_ids[
                                                              -1].product_id.list_price * rec.rate
            elif rec.move_type == 'in_invoice':
                if len(rec.invoice_line_ids) >= 1 and rec.is_exchange:
                    rec.invoice_line_ids[-1].price_unit = rec.invoice_line_ids[
                                                              -1].product_id.standard_price * rec.rate
