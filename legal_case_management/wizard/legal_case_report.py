# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: LAJINA.K.V (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class LegalCaseReport(models.TransientModel):
    """Legal Case Report"""
    _name = 'legal.case.report'
    _description = 'Wizard for printing reports'

    lawyer_id = fields.Many2one('hr.employee', string='Lawyer',
                                domain=[('is_lawyer', '=', True),
                                        ('parent_id', '=', False)],
                                help="Available Lawyers")
    client_id = fields.Many2one('res.partner', string='Client',
                                help='Available Clients')
    court_id = fields.Many2one('legal.court', string="Court",
                               help=" Available Courts")
    judge_id = fields.Many2one('res.partner', string='Judge',
                               domain="[('is_judge', '=', True)]",
                               help='Available Judges')
    start_date = fields.Date("Start Date", help="Start Date")
    end_date = fields.Date("End Date", help="End Date")
    state = fields.Selection(
        [('draft', 'Draft'), ('in_progress', 'In progress'),
         ('invoiced', 'Invoiced'), ('reject', 'Reject'),
         ('won', 'Won'), ('lost', 'Lost'), ('cancel', 'Cancel')],
        string='State')
    payment_method = fields.Selection(selection=[
        ('trial', "Per Trial"),
        ('case', "Per Case"),
        ('out_of_court', "Out of Court")], string='Payment Method')

    def print_pdf_report(self):
        """ wizard for print pdf report"""
        data = {
            'lawyer_id': self.lawyer_id.name,
            'client_id': self.client_id.name,
            'court_id': self.court_id.name,
            'judge_id': self.judge_id.name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'payment_method': self.payment_method,
            'state': self.state
        }
        return self.env.ref(
            'legal_case_management.legal_case_wizard_action_report').\
            report_action(None, data=data)
