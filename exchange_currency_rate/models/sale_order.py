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


class SaleOrder(models.Model):
    """This class extends the base 'sale.order' model to introduce a
    new field, 'is_exchange',which allows users to manually apply an exchange
    rate for a transaction. When this option is enabled,users can specify the
    exchange rate through the 'rate' field."""
    _inherit = 'sale.order'

    company_currency_id = fields.Many2one(
        string='Company Currency',
        related='company_id.currency_id', readonly=True,
        help='Store the Company Currency'
    )

    is_exchange = fields.Boolean(string='Apply Manual Currency',
                                 compute="_compute_is_exchange",
                                 inverse="_inverse_is_exchange",
                                 store=True,
                                 help='Enable the boolean field to display '
                                      'rate field')
    rate = fields.Float(string='Rate', help='specify the currency rate',
                        default=1)

    @api.depends('company_id', 'currency_id')
    def _compute_is_exchange(self):
        """ When the Currency is changed back to company currency, the boolean field is disabled """
        for order in self:
            if order.company_currency_id == order.currency_id:
                order.is_exchange = False

    def _inverse_is_exchange(self):
        pass

    @api.onchange('is_exchange')
    def _onchange_is_exchange(self):
        """ Update Rate when is_exchange is Enabled."""
        if self.is_exchange:
            self.rate = self.env['res.currency']._get_conversion_rate(
                from_currency=self.company_currency_id,
                to_currency=self.currency_id,
                company=self.company_id,
                date=self.date_order,
            )
