# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: fasluca(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    discount = fields.Float('Discount', readonly=True)

    def _select(self):
        res = super(AccountInvoiceReport,self)._select()
        select_str = res + """, sub.discount AS discount """
        return select_str

    def _sub_select(self):
        res = super(AccountInvoiceReport,self)._sub_select()
        select_str = res + """,SUM ((invoice_type.sign * ail.quantity) / (u.factor * u2.factor) * ail.price_unit *
         ail.discount / 100) AS discount"""
        return select_str