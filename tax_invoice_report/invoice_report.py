# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Treesa Maria Jude(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    tax_amount = fields.Float(string='Total Tax', readonly=True)
    total_amount = fields.Float(string='Total With Tax', readonly=True)
    number = fields.Char(string='Invoice Number')

    def _select(self):
        return super(AccountInvoiceReport, self)._select() \
               + ", sub.tax_amount as tax_amount,sub.total_amount as total_amount,sub.number"

    def _sub_select(self):
        return super(AccountInvoiceReport, self)._sub_select() \
               + ",ai.amount_tax as tax_amount, ai.amount_total as total_amount,ai.number as number"
    
    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + ", ai.number"
