# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen(odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models


class AccountInvoiceReport(models.Model):
    """This class inherits the model 'account.invoice.report'"""
    _inherit = 'account.invoice.report'

    discount = fields.Float('Discount', readonly=True,
                            help="Specify the discount.")

    def _select(self):
        """This allows the report to include the discount information in its
         SQL query when fetching data from the database. """
        res = super(AccountInvoiceReport, self)._select()
        select_str = res + """, line.discount AS discount """
        return select_str
