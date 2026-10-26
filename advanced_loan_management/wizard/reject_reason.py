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


class RejectReasonWizard(models.TransientModel):
    """Reject reasons from the company side"""
    _name = 'reject.reason'
    _description = 'Reject Reasons From The Company Side'

    reason = fields.Text(string="Reason", help="Reason Content", required=True)
    loan = fields.Char(string="Loan", help="Invisible Field")

    def action_reject_reason_txt(self):
        """Attach Reject Reason"""
        loan_request = self.env['loan.request'].search(
            [('name', '=', self.loan)])
        loan_request.write({
            'state': 'rejected',
            'reject_reason': self.reason
        })
