# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.report import report_sxw
from openerp.osv import osv


class WithoutTax(report_sxw.rml_parse):

    _inherit = 'account.tax'

    def __init__(self, cr, uid, name, context=None):
        super(WithoutTax, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_details': self.get_details,


        })
        self.context = context

    def get_details(self, tax, subtotal):
        print tax
        total_amount = 0
        tax_amount = []
        for i in tax:
                tax_amount.append(i.amount)
                print tax_amount
        for j in range(0, len(tax)):
                total_amount = (tax_amount[j] / 100 * subtotal) + total_amount
                print total_amount
        total = total_amount + subtotal
        return total


class AccountReport(osv.AbstractModel):
    _name = 'report.untaxed_saleorder_report.invoice_account_report'
    _inherit = 'report.abstract_report'
    _template = 'untaxed_saleorder_report.invoice_account_report'
    _wrapped_report_class = WithoutTax


class SaleReport(osv.AbstractModel):
    _name = 'report.untaxed_saleorder_report.invoice_sale_report'
    _inherit = 'report.abstract_report'
    _template = 'untaxed_saleorder_report.invoice_sale_report'
    _wrapped_report_class = WithoutTax
