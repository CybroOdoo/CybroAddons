# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import datetime, date

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RecurringPaymentsWizard(models.TransientModel):
    _name = 'recurring.payments.wizard'
    _description = 'Recurring Payment Wizard'

    recurring_lines = fields.One2many('account.recurring.entries.line', 'p_id')
    date_from = fields.Date('Starting Date', default=date.today())
    recurring_tmpl_ids = fields.Many2many('account.recurring.payments',
                                          string='Recurring Template')

    @api.model
    def default_get(self, fields):
        result = super(RecurringPaymentsWizard, self).default_get(fields)
        self.get_remaining_entries()
        return result

    @api.onchange('date_from', 'recurring_tmpl_ids')
    def get_remaining_entries(self):
        if self.date_from:
            if self.recurring_tmpl_ids:
                data = self.env['account.recurring.payments'].search(
                    [('state', '=', 'running'),
                     ('id', 'in', self.recurring_tmpl_ids.ids)])
            else:
                data = self.env['account.recurring.payments'].search(
                    [('state', '=', 'running')])
            entries = self.env['account.move'].search(
                [('recurring_ref', '!=', False)])
            journal_dates = []
            journal_codes = []
            remaining_dates = []
            for entry in entries:
                journal_dates.append(str(entry.date))
                if entry.recurring_ref:
                    journal_codes.append(str(entry.recurring_ref))
            today = datetime.today()
            converted_date_from = datetime.strptime(str(self.date_from),
                                                    '%Y-%m-%d')
            for line in data:
                if line.date:
                    recurr_dates = []
                    start_date = datetime.strptime(str(line.date), '%Y-%m-%d')
                    while start_date <= today:
                        recurr_dates.append(str(start_date.date()))
                        if line.recurring_period == 'days':
                            start_date += relativedelta(
                                days=line.recurring_interval)
                        elif line.recurring_period == 'weeks':
                            start_date += relativedelta(
                                weeks=line.recurring_interval)
                        elif line.recurring_period == 'months':
                            start_date += relativedelta(
                                months=line.recurring_interval)
                        else:
                            start_date += relativedelta(
                                years=line.recurring_interval)
                    for rec in recurr_dates:
                        recurr_code = str(line.id) + '/' + str(rec)
                        converted_rec = datetime.strptime(str(rec), '%Y-%m-%d')
                        if recurr_code not in journal_codes and converted_rec >= converted_date_from:
                            remaining_dates.append({
                                'date': rec,
                                'template_name': line.name,
                                'amount': line.amount,
                                'tmpl_id': line.id,
                            })
            child_ids = self.recurring_lines.create(remaining_dates)
            self.recurring_lines = child_ids.ids
        else:
            self.recurring_lines = False

    def generate_payment(self):
        data = self.recurring_lines
        if not data:
            raise UserError(_("There is no remaining payments"))
        for line in data:
            tmpl_id = line.tmpl_id
            recurr_code = str(tmpl_id.id) + '/' + str(line.date)
            line_ids = [(0, 0, {
                'account_id': tmpl_id.credit_account.id,
                'partner_id': tmpl_id.partner_id.id,
                'credit': line.amount,
                'analytic_account_id': tmpl_id.analytic_account_id.id,
            }), (0, 0, {
                'account_id': tmpl_id.debit_account.id,
                'partner_id': tmpl_id.partner_id.id,
                'debit': line.amount,
                'analytic_account_id': tmpl_id.analytic_account_id.id,
            })]

            vals = {
                'date': line.date,
                'recurring_ref': recurr_code,
                'company_id': self.env.user.company_id.id,
                'journal_id': tmpl_id.journal_id.id,
                'ref': line.template_name,
                'narration': 'Recurring entry',
                'line_ids': line_ids
            }
            move_id = self.env['account.move'].create(vals)
            if tmpl_id.journal_state == 'posted':
                move_id.post()


class GetAllRecurringEntries(models.TransientModel):
    _name = 'account.recurring.entries.line'
    _description = 'Account Recurring Entries Line'

    date = fields.Date('Date')
    template_name = fields.Char('Name')
    amount = fields.Float('Amount')
    tmpl_id = fields.Many2one('account.recurring.payments', string='id')
    p_id = fields.Many2one('recurring.payments.wizard')