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


class ResPartner(models.Model):
    """Add new tab to display partner's loan count"""
    _inherit = "res.partner"

    def _compute_partner_loans(self):
        """This computes the loan count of a partner."""
        for partner in self:
            partner.loan_count = self.env['loan.request'].search_count(
                [('partner_id', '=', partner.id),
                 ('state', 'in', ('disbursed', 'closed'))])

    loan_count = fields.Integer(string="Loan Count",
                                compute='_compute_partner_loans',
                                help="Displays numbers of loans "
                                     "ongoing and closed by the employee")

    def action_view_loans(self):
        """Returns loan records of current employee"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Loans',
            'view_mode': 'list',
            'res_model': 'loan.request',
            'domain': [('partner_id', '=', self.id)],
            'context': "{'create': False}"
        }

