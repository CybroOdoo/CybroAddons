#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    """This class extends the base 'purchase.order' model to introduce a
    new field, 'is_exchange', which allows users to manually apply an exchange
    rate for a transaction. When this option is enabled, users can specify
    the exchange rate through the 'rate' field."""
    _inherit = 'purchase.order'

    company_currency_id = fields.Many2one(
        string='Company Currency',
        related='company_id.currency_id',
        readonly=True,
        help="Store the company currency.",
    )
    is_exchange = fields.Boolean(
        string='Apply Manual Currency',
        help="Allows users to manually apply an exchange rate.",
    )
    rate = fields.Float(
        string='Rate',
        help="Specify the currency exchange rate.",
        default=1.0,
    )

    @api.constrains('currency_id', 'is_exchange')
    def _onchange_different_currency(self):
        """ When the Currency is changed back to company currency, the boolean field is disabled """
        for order in self:
            if order.company_currency_id == order.currency_id and order.is_exchange:
                order.is_exchange = False

    @api.onchange('currency_id', 'company_currency_id')
    def _onchange_currency_id(self):
        """ Form-level onchange to reset is_exchange when currency matches company currency """
        if self.currency_id == self.company_currency_id and self.is_exchange:
            self.is_exchange = False

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
