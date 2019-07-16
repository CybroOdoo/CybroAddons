# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Muhamed Amal(<http://www.cybrosys.com>)
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
from openerp import models, fields
from openerp.exceptions import UserError
from openerp.tools.translate import _


class AddExpensePaymentButton(models.Model):
    _inherit = 'hr.expense'

    payment_id = fields.Many2one('account.payment', string='Payment Reference', copy=False)
    check_payment = fields.Boolean(default=False, copy=False)

    def hr_expense_payment(self, cr, uid, ids, context=None):
        expense = self.browse(cr, uid, ids, context)
        if not expense.check_payment:
            total = expense.total_amount
            partner_id = expense.employee_id.address_home_id
            payment_creation_obj = self.pool.get('account.payment')
            vals_payment = {'communication': False,
                            'journal_id': 5,
                            'destination_journal_id': False,
                            'currency_id': 21,
                            'partner_type': u'supplier',
                            'state': 'draft',
                            'payment_type': u'outbound',
                            'amount': total,
                            'partner_id': partner_id.id,
                            'payment_method_id': 2}
            expense.payment_id = payment_creation_obj.create(cr, uid, vals_payment, context)
            expense.check_payment = True
        else:
            raise UserError(_('You have already created a payment'))

    def hr_expense_reconcile(self, cr, uid, ids, context=None):
        if self.browse(cr, uid, ids, context).check_payment:
            if self.browse(cr, uid, ids, context).payment_id.state == 'draft':
                raise UserError(_('Please validate payment for this employee'))
            else:
                return {
                    'name': 'Reconcile',
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move.line',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_id': 'hr_expense_payment',
                    'domain': [('account_id.name', '=', 'Creditors'), ('reconciled', '=', False)]
                }
        else:
            raise UserError(_('Please create a payment for this employee'))