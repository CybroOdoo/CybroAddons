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


class CalculateIncentive(models.Model):
    """
    This class represents the model for calculating and tracking sales
    incentives. Each instance of this model corresponds to a specific
    calculation of incentives for a salesperson based on their achieved goals.
    """
    _name = 'calculate.incentive'
    _description = 'Calculate Incentive'

    salesperson_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        help='salesperson associated with the scheme'
    )
    goal = fields.Float(
        string='Target',
        help='Target amount that the salesperson needs to achieve.'
    )
    achieved = fields.Float(
        string='Achievement',
        help='Achieved amount by the salesperson.'
    )
    achievement_percentage = fields.Float(
        string='Achievement %',
        help='Achievement in percentage.'
    )
    incentive = fields.Float(
        string='Incentive',
        help='Total incentive earned by the salesperson.')
    check = fields.Boolean(string="Check",
                           help="Used to check if it is paid or not")
    start_date = fields.Date(
        string='Start Date',
        help='The start date for the period associated with the goal.'
    )
    end_date = fields.Date(
        string='End Date',
        help='The end date for the period associated with the goal.'
    )
    date_check = fields.Boolean(
        compute='_compute_date_check',
        help='Computed field indicating whether the dates meet end date.')
    status = fields.Selection(
        [('unpaid', 'Not Paid'),
         ('submit', 'Submitted To Accountant'), ('paid', 'Paid'),
         ('reject', 'Rejected')], string='State', default='unpaid',
        help='Status of the record.'
    )

    def _compute_date_check(self):
        """
            Compute the date check for each record.
            This method iterates over the records and checks if the end date
            is less than or equal to the current date. If true, it sets the
            date_check field to True; otherwise, it sets it to False.
            :return: None
            """
        for rec in self:
            rec.date_check = False
            if rec.end_date <= fields.Date.today():
                rec.date_check = True

    def action_submit_to_accountant(self):
        """
        Creates an 'approve.incentive' record for the calculated incentive
        amount, and updates the status to 'Submitted To Accountant'.
        If the incentive amount is 0.0, a UserError is raised.
        """
        if self.incentive == 0.0:
            raise UserError(_('Incentive amount is 0.0'))
        data = {
            'salesperson_id': self.salesperson_id.id,
            'goal': self.goal,
            'achieved': self.achieved,
            'achievement_percentage': self.achievement_percentage,
            'incentive': self.incentive,
            'status': 'submit',
            'start_date': self.start_date,
            'end_date': self.end_date,
        }
        self.env['approve.incentive'].create(data)
        self.check = True
        self.status = 'submit'
