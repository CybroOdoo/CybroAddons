# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Alvin F (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class LoanType(models.Model):
    """Create different types of Loans, And can wisely choose while requesting
     for loan"""
    _name = 'loan.type'
    _inherit = ['mail.thread']
    _description = 'Loan Type'

    name = fields.Char(string='Name', help="LoanType Name", required=True)
    loan_amount = fields.Integer(string='Loan Amount', help="Loan Amount", required=True)
    tenure = fields.Integer(string='Tenure', default='1',
                            help="Amortization period")
    tenure_plan = fields.Char(string="Tenure Plan", default='Monthly',
                              readonly=True, help="EMI payment plan")
    interest_rate = fields.Float(string='Interest Rate',
                                 help="Loan Interest Rate")
    disbursal_amount = fields.Float(string='Disbursal Amount',
                                    compute='_compute_disbursal_amount',
                                    help="Total Amount To Be Disbursed")
    documents_ids = fields.Many2many('loan.documents',
                                     string="Documents",
                                     help="Personal Proofs")
    processing_fee = fields.Integer(string="Processing Fee",
                                    help="Amount For Initializing The Loan")
    note = fields.Text(string="Criteria", help="Criteria for approving "
                                               "loan requests")
    company_id = fields.Many2one('res.company', string='Company',
                                 readonly=True, help="Company Name",
                                 default=lambda self: self.env.company, )

    @api.depends('processing_fee', 'loan_amount')
    def _compute_disbursal_amount(self):
        """Calculating amount for disbursing"""
        for rec in self:
            rec.disbursal_amount = rec.loan_amount - rec.processing_fee
