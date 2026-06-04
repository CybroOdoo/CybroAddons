# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

class PurchaseOrder(models.Model):
    """This class extends the base 'purchase.order' model to introduce a
    new field, 'is_exchange',which allows users to manually apply an exchange
    rate for a transaction. When this option is enabled, users can specify
    the exchange rate through the 'rate' field."""
    _inherit = 'purchase.order'

    company_currency_id = fields.Many2one(
        string='Company Currency',
        related='company_id.currency_id', readonly=True, help="To store the Company Currency")
    is_exchange = fields.Boolean(string='Apply Manual Currency', help='allows users to manually apply an exchange rate')
    rate = fields.Float(string='Rate', help='specify the rate', default=1)

    @api.constrains('company_currency_id', 'currency_id')
    def _onchange_different_currency(self):
        """ When the Currency is changed back to company currency, the boolean field is disabled """
        if self.company_currency_id == self.currency_id:
            if self.is_exchange:
                self.is_exchange = False

    @api.onchange('is_exchange')
    def _onchange_is_exchange(self):
        """ Update Rate when is_exchange is Enabled."""
        if self.is_exchange:
            self.rate = self.env['res.currency']._get_conversion_rate(
                from_currency=self.company_currency_id,
                to_currency=self.currency_id,
                company=self.company_id,
                date=self.date_order)
