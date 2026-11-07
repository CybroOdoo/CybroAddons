# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models


class LegalCaseReport(models.TransientModel):
    """Wizard to generate legal case report based on filters"""
    _name = 'legal.case.report'
    _description = 'Legal Case Report Wizard'

    lawyer_id = fields.Many2one('hr.employee', string='Lawyer',
                                domain=[('is_lawyer', '=', True)],
                                help='Filter cases by lawyer')
    client_id = fields.Many2one('res.partner', string='Client',
                                help='Filter cases by client')
    court_id = fields.Many2one('legal.court', string='Court',
                               help='Filter cases by court')
    judge_id = fields.Many2one('res.partner', string='Judge',
                               help='Filter cases by judge')
    start_date = fields.Date(string='Start Date',
                             help='Filter cases by start date')
    end_date = fields.Date(string='End Date',
                           help='Filter cases by end date')
    payment_method = fields.Selection([
        ('trial', "Per Trial"),
        ('case', "Per Case"),
        ('out_of_court', "Out of Court")
    ], string='Payment Method', help='Filter cases by payment method')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('invoiced', 'Invoiced'),
        ('won', 'Won'),
        ('lost', 'Lost'),
        ('cancel', 'Cancelled'),
        ('reject', 'Rejected')
    ], string='State', help='Filter cases by state')

    def action_print_report(self):
        """Print the legal case details report"""
        self.ensure_one()
        data = {
            'lawyer_id': self.lawyer_id.name if self.lawyer_id else False,
            'client_id': self.client_id.name if self.client_id else False,
            'court_id': self.court_id.name if self.court_id else False,
            'judge_id': self.judge_id.name if self.judge_id else False,
            'start_date': str(self.start_date) if self.start_date else False,
            'end_date': str(self.end_date) if self.end_date else False,
            'payment_method': self.payment_method or False,
            'state': self.state or False,
        }
        return self.env.ref(
            'legal_case_management.legal_case_wizard_action_report'
        ).report_action([], data=data, config=False)
