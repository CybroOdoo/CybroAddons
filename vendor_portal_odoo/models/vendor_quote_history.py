# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
from odoo import fields, models


class VendorQuoteHistory(models.Model):
    """Vendor Quotation History"""
    _name = 'vendor.quote.history'
    _description = "Vendor Quotation History"
    _rec_name = 'vendor_id'

    vendor_id = fields.Many2one('res.partner',
                                domain="[('is_registered', '=', True)]",
                                string="Vendor", help="Registered vendors")
    quoted_price = fields.Monetary(currency_field='currency_id',
                                   string="Quoted Price",
                                   help="The price quoted by vendor")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True,
                                  default=lambda
                                      self: self.env.user.company_id.currency_id,
                                  help="The current company currency")
    estimate_date = fields.Date(string="Estimate date",
                                help="Estimated date of the quotation")
    note = fields.Text(string="Note", help="Additional notes of the quote")
    quote_id = fields.Many2one('vendor.rfq', string="Quote",
                               help='The related field from vendor rfq')
