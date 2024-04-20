# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: ASWIN A K (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1) It is forbidden to publish, distribute, sublicense, or sell
#    copies of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#    THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from odoo import fields, models, _
from odoo.exceptions import UserError


class SalesIncentive(models.Model):
    """
    This class represents the 'approve.incentive' model, which is used to
    approve and manage sales incentives for salespersons. It includes fields for
    tracking salesperson details, incentive information, and the approval
    status.
    """
    _name = 'approve.incentive'
    _description = 'Approve Incentive'
    _rec_name = 'salesperson_id'

    salesperson_id = fields.Many2one(
        'res.users', string='Salesperson',
        help='Salesperson associated with the scheme.')
    name = fields.Char(string='Name')
    goal = fields.Float(
        string='Target',
        help='Target amount that the salesperson needs to achieve.')
    achieved = fields.Float(string='Achievement',
                            help='Achieved amount by the salesperson.')
    achievement_percentage = fields.Float(string='Achievement %',
                                          help='Achievement in percentage.')
    incentive = fields.Float(string='Incentive',
                             help='Total incentive earned by the salesperson.')
    status = fields.Selection([('unpaid', 'Not Paid'),
                               ('submit', 'Submitted To Accountant'),
                               ('paid', 'Paid'), ('reject', 'Rejected')],
                              string='State', default='unpaid',
                              help='Status of the incentive.'
                              )
    journal_id = fields.Many2one('account.journal',
                                 string='Journal',
                                 help='Select the accounting journal.'
                                 )
    check = fields.Boolean(string="Check",
                           help="Used to check if it is paid or not")
    debit_account_id = fields.Many2one(
        'account.account',
        domain=[('deprecated', '=', False)],
        string='Debit account',
        help='Select the debit account.'
    )
    credit_account_id = fields.Many2one(
        'account.account',
        domain=[('deprecated', '=', False)],
        string='Credit account',
        help='Select the credit account.'
    )
    start_date = fields.Date(
        string='Start Date',
        help='The start date for the period associated with the scheme.')
    end_date = fields.Date(
        string='End Date',
        help='The end date for the period associated with the scheme.'
    )

    def action_approve(self):
        """
            Approves the incentive and creates account_move with the
            corresponding values. Changes the state.
        """
        if not (self.journal_id
                and self.debit_account_id and self.credit_account_id):
            raise UserError(
                _('You must enter journal, debit account and credit account'))
        lines = [fields.Command.create({
            'account_id': self.credit_account_id.id,
            'partner_id': self.salesperson_id.partner_id.id,
            'credit': self.incentive,
            'name': 'Incentive'
        }), fields.Command.create({
            'account_id': self.debit_account_id.id,
            'partner_id': self.salesperson_id.partner_id.id,
            'debit': self.incentive
        })]
        val = {
            'date': fields.Date.today(),
            'journal_id': self.journal_id.id,
            'line_ids': lines
        }
        self.env['account.move'].create(val)
        calc = self.env['calculate.incentive'].search(
            [('salesperson_id', '=', self.salesperson_id.id),
             ('start_date', '=', self.start_date),
             ('end_date', '=', self.end_date),
             ('status', '=', 'submit')])
        self.write({
            'status': 'paid',
            'check': True
        })
        calc.write({
            'status': 'paid',
            'check': True
        })

    def action_rejected(self):
        """
            Rejects the incentive request and changes the state.
        """
        self.write({
            'status': 'reject',
            'check': True
        })
        calc = self.env['calculate.incentive'].search(
            [('salesperson_id', '=', self.salesperson_id.id),
             ('start_date', '=', self.start_date),
             ('end_date', '=', self.end_date),
             ('status', '=', 'submit')])
        calc.write({
            'status': 'reject',
            'check': True
        })
