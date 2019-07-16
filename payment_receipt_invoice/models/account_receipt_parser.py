# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Niyas Raphy(<http://www.cybrosys.com>)
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
import json


class AccountReceiptParser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(AccountReceiptParser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_details': self.get_details,
            'get_details_inv': self.get_details_inv,
        })
        self.context = context

    def get_details_inv(self, doc):
        lines = []
        acc_inv = self.pool.get('account.invoice').search(self.cr, self.uid, [('id', '=', doc.id)])
        acc_inv_rec = self.pool.get('account.invoice').browse(self.cr, self.uid, acc_inv, context=None)
        total_amount = acc_inv_rec.amount_total
        if acc_inv_rec.state == 'draft':
            balance_amount = total_amount
        else:
            balance_amount = acc_inv_rec.residual
        paid = total_amount - balance_amount
        vals = {
            'total_amount': total_amount,
            'balance_amount': balance_amount,
            'paid': paid,
        }
        lines.append(vals)
        return lines

    def get_details(self, doc):
        lines = []
        acc_inv = self.pool.get('account.invoice').search(self.cr, self.uid, [('id', '=', doc.id)])
        acc_inv_rec = self.pool.get('account.invoice').browse(self.cr, self.uid, acc_inv, context=None)
        if acc_inv_rec.payments_widget != 'false':
            d = json.loads(acc_inv_rec.payments_widget)
            for payment in d['content']:
                vals = {
                    'memo': payment['name'],
                    'amount': payment['amount'],
                    'method': payment['journal_name'],
                    'date': payment['date'],
                }
                lines.append(vals)
        return lines


class PrintReport(osv.AbstractModel):
    _name = 'report.payment_receipt_invoice.report_payment'
    _inherit = 'report.abstract_report'
    _template = 'payment_receipt_invoice.report_payment'
    _wrapped_report_class = AccountReceiptParser


