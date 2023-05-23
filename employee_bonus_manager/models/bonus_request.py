# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amaya Aravind (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class BonusRequest(models.Model):
    """
    This class is created for model bonus.request. It contains fields and
    functions for the model.
    Methods:
        create(self, vals):
            override create function for generating sequence number for the new
            records of the model.
        action_confirm(self):
            actions to perform when clicking on the 'Confirm' button.
        action_department_approve(self):
            actions to perform when clicking on the 'Approve by Department'
            button.
        action_manager_approve(self):
            actions to perform when clicking on the 'Approve by Manager'
            button.
        action_reject(self):
            actions to perform when clicking on the 'Reject' button.
        action_reset_to_draft(self):
            actions to perform when clicking on the 'Reset to Draft' button.
    """
    _name = 'bonus.request'
    _description = 'Bonus Request'
    _inherit = 'mail.thread'
    _rec_name = 'reference_no'

    reference_no = fields.Char(string='Reference Number', copy=False,
                               help='Sequence number for the bonus request.')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'),
         ('department_approved', 'Department Approved'),
         ('manager_approved', 'Manager Approved'), ('rejected', 'Rejected')],
        string='State', default='draft', copy=False, tracking=True,
        help='State of the bonus request.')
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True, tracking=True,
        help='The bonus will be given to this employee')
    user_id = fields.Many2one(
        'res.users', string='User', related='employee_id.user_id',
        help='The user of the employee(If any)')
    department_id = fields.Many2one('hr.department', string='Department',
                                    related='employee_id.department_id',
                                    help='The department of the employee.')
    job_id = fields.Many2one(
        'hr.job', string='Job', related='employee_id.job_id',
        help='Job of the employee')
    bonus_reason_id = fields.Many2one(
        'bonus.reason', string='Bonus Reason', required=True,
        help='Reason for providing the Bonus.')
    confirmed_user_id = fields.Many2one(
        'res.users', string='Confirmed by', readonly=True, copy=False,
        help='This field will record the name of the person who confirmed '
             'the bonus request.')
    confirmed_date = fields.Date(
        string='Confirmed Date', readonly=True, copy=False, tracking=True,
        help='Confirmed date of bonus request')
    bonus_amount = fields.Float(string='Bonus Amount', tracking=True,
                                help='This amount will be given as the bonus.')
    currency_id = fields.Many2one(
        'res.currency', string='Company Currency',  required=True,
        readonly=True,
        default=lambda self: self.env.user.company_id.currency_id,
        help='Company Currency')
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True,
        default=lambda self: self.env.company, help='Company of the user.')
    department_approved_date = fields.Date(
        string='Department Approved Date', readonly=True, copy=False,
        help='Date on which the bonus request is approved by the Department.')
    manager_approved_date = fields.Date(
        string='Manager Approved Date', readonly=True, copy=False,
        help='Date on which the bonus request is approved by the Manager.')
    department_manager_id = fields.Many2one(
        'res.users', string='Department Manager', readonly=True, copy=False,
        help='Name of the Department Head, who approved the bonus request.')
    hr_manager_id = fields.Many2one(
        'res.users', string='Manager', readonly=True, copy=False,
        help='Name of the Manager, who approved the bonus request.')

    @api.model
    def create(self, vals):
        """ Override the create function for creating new sequence number.
        Args:
           vals (dict): values for creating new records.
       Returns:
            models.Model: the created records of 'bonus.request'.
        """
        if vals.get('reference_no', 'New') == 'New':
            vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                'bonus.request') or 'New'
        res = super(BonusRequest, self).create(vals)
        return res

    def action_confirm(self):
        """
        Function for the 'Confirm' button to change the state to 'confirmed',
        and update the confirmed user and date.
        """
        self.write({
            'state': 'confirmed',
            'confirmed_user_id': self._uid,
            'confirmed_date': fields.Datetime.today()
        })

    def action_department_approve(self):
        """
        Function for the 'Approve by Department' button to change the state to
        'department_approved', and update the department manager and approved
        time.
        """
        self.write({
            'state': 'department_approved',
            'department_manager_id': self._uid,
            'department_approved_date': fields.Datetime.today()
        })

    def action_manager_approve(self):
        """
        Function for the 'Approve by Manager' button to change the state to
        'manager_approved', and update the HR manager and approved date & time.
        """
        self.write({
            'state': 'manager_approved',
            'hr_manager_id': self._uid,
            'manager_approved_date': fields.Datetime.today()
        })

    def action_reject(self):
        """
        Function for the 'Reject' button to change the state to 'rejected'.
        """
        self.state = 'rejected'

    def action_reset_to_draft(self):
        """
        Function for the 'Reset to Draft' button to change the state to 'draft'
        and reset the fields which are to be updated on changing the states.
        """
        self.write({
            'state': 'draft',
            'confirmed_user_id': False,
            'confirmed_date': False,
            'department_manager_id': False,
            'department_approved_date': False,
            'hr_manager_id': False,
            'manager_approved_date': False
        })
