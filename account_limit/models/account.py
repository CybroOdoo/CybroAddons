# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nikhil krishnan(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

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

from odoo import fields, api, _, models
from odoo.exceptions import Warning


class AccountAccount(models.Model):
    _inherit = 'account.account'

    @api.multi
    def get_credit_debit_balance(self):
        for obj in self:
            credit = 0
            debit = 0
            account_lines = self.env['account.move.line'].search([('account_id', '=', obj.id)])
            for line in account_lines:
                credit += line.credit
                debit += line.debit
            obj.credit = credit
            obj.debit = debit
            obj.balance = debit - credit

    credit = fields.Float(string='Credit', compute='get_credit_debit_balance')
    debit = fields.Float(string='Debit', compute='get_credit_debit_balance')
    balance = fields.Float(string='Balance', compute='get_credit_debit_balance')
    account_credit_limit = fields.Float(string='Credit Limit', Help="Credit Limit for this particular Account.")


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def create(self, vals):
        credit = 0
        debit = 0
        if "line_ids" in vals.keys():
            for line in vals['line_ids']:
                if line[2]['credit']:
                    account = self.env['account.account'].browse(line[2]['account_id'])
                    account_lines = self.env['account.move.line'].search([('account_id', '=', account.id)])
                    for lines in account_lines:
                        credit += lines.credit
                        debit += lines.debit
                    if account.account_credit_limit:
                        if (credit+line[2]['credit'] - debit) > account.account_credit_limit:
                            raise Warning(_('Limit will Exceed .! \n Making this transaction will exceed the limit '
                                            'defined for " %s " account') % account.name)
        result = super(AccountMove, self).create(vals)
        return result

    @api.multi
    def write(self, vals):
        if "line_ids" in vals.keys():
            for line in vals['line_ids']:
                account_lines = self.env['account.move.line'].browse(line[1])
                if line[2]:
                    if 'account_id' in line[2]:
                        if line[2]['account_id']:
                            account = self.env['account.account'].browse(line[2]['account_id'])
                            if account.account_credit_limit:
                                if 'debit' in line[2]:
                                    new_debit = line[2]['debit']
                                else:
                                    new_debit = account_lines.debit
                                if 'credit' in line[2]:
                                    new_credit = line[2]['credit']
                                else:
                                    new_credit = account_lines.credit
                                if (account.credit + new_credit - new_debit - account.debit) > account.account_credit_limit:
                                    raise Warning(
                                        _('Limit will Exceed .! \n Making this transaction will exceed the limit '
                                          'defined for " %s " account') % account.name)
                    else:
                        account = account_lines.account_id
                        if account.account_credit_limit:
                            if 'debit' in line[2]:
                                if line[2]['debit']:
                                    old_debit = account_lines.debit
                                    if (account.credit - line[2]['debit'] - account.debit + old_debit) > account.account_credit_limit:
                                        raise Warning(
                                            _('Limit will Exceed .! \n Making this transaction will exceed the limit '
                                              'defined for " %s " account') % account.name)
                            if 'credit' in line[2]:
                                if line[2]['credit']:
                                    old_credit = account_lines.credit
                                    if (account.credit+line[2]['credit']-account.debit-old_credit) > account.account_credit_limit:
                                        raise Warning(
                                            _('Limit will Exceed .! \n Making this transaction will exceed the limit '
                                              'defined for " %s " account') % account.name)
        result = super(AccountMove, self).write(vals)
        return result
