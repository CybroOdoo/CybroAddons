#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    """Add the line discount to the invoice analysis."""
    _inherit = 'account.invoice.report'

    discount = fields.Float(
        string='Discount %', readonly=True, aggregator='avg',
        help="Discount percentage of the line.")

    def _select_list(self, table):
        """Add the line discount to the invoice analysis query."""
        return super()._select_list(table) + [
            SQL("%s AS discount", table.discount)]
