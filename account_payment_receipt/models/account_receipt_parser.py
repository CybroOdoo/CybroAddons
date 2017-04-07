# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Niyas Raphy(<http://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo.report import report_sxw
from odoo.osv import osv
from odoo import api
from odoo.http import request
import json


class AccountReceiptParser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(AccountReceiptParser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_details': self.get_details,
        })
        self.context = context

    @api.multi
    def get_details(self, doc):
        lines = []
        acc_inv = request.env['account.invoice']
        acc_inv_rec = acc_inv.search([('number', '=', doc.number)])
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
    _name = 'report.account_payment_receipt.report_payment'
    _inherit = 'report.abstract_report'
    _template = 'account_payment_receipt.report_payment'
    _wrapped_report_class = AccountReceiptParser


