# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class VendorQuoteHistory(models.Model):
    """Vendor Quotation History"""
    _name = 'vendor.quote.history'
    _description = "Vendor Quotation History"
    _rec_name = 'vendor_id'

    vendor_id = fields.Many2one('res.partner',
                                domain="[('is_registered', '=', True)]",
                                string="Vendor",
                                help="Select Vendor")
    quoted_price = fields.Monetary(currency_field='currency_id',
                                   help="Quoted Price")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  help="Currency",
                                  required=True,
                                  default=lambda
                                      self: self.env.user.company_id.currency_id)
    estimate_date = fields.Date(string="Estimate date", help="Estimated Date")
    note = fields.Text(string="Note", help="Additional Note")
    quote_id = fields.Many2one('vendor.rfq', help="Quote ID")
