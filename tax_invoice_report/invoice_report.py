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

from odoo import fields, models,api, _


class Invoicelinecount(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def get_count_as(self):
        for inv in self:
            inv.count_line = len(inv.invoice_line_ids)
            inv.count_line1 = len(inv.invoice_line_ids)
            inv.write({'count_line1': len(inv.invoice_line_ids)})

    @api.multi
    def _write(self, vals):
        for i in self:
            vals.update({'count_line1': len(i.invoice_line_ids)})
        pre_not_reconciled = self.filtered(lambda invoice: not invoice.reconciled)
        pre_reconciled = self - pre_not_reconciled
        res = super(Invoicelinecount, self)._write(vals)
        reconciled = self.filtered(lambda invoice: invoice.reconciled)
        not_reconciled = self - reconciled
        (reconciled & pre_reconciled).filtered(lambda invoice: invoice.state == 'open').action_invoice_paid()
        (not_reconciled & pre_not_reconciled).filtered(lambda invoice: invoice.state == 'paid').action_invoice_re_open()
        return res

    count_line = fields.Integer(string="Count", compute="get_count_as", store=True)
    count_line1 = fields.Integer(string="Count1", default=1)


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    amount_taxes = fields.Float(string='Total Tax', readonly=True)
    amount_totals = fields.Float(string='Total With Tax', readonly=True)
    number = fields.Char(string='Invoice Number')

    def _select(self):
        return super(AccountInvoiceReport, self)._select() \
               + ", sub.amount_taxes as amount_taxes,sub.amount_totals as amount_totals,sub.number"

    def _sub_select(self):
        return super(AccountInvoiceReport, self)._sub_select() \
               + ",(ai.amount_tax)/(ai.count_line1) AS amount_taxes, " \
                 "(ai.amount_total)/(ai.count_line1) as amount_totals ,ai.number"
    
    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + ", ai.number"
