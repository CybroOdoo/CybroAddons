# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sabeel (odoo@cybrosys.com)
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
from odoo import fields, models


class ResPartner(models.Model):
    """Add new tab to display partner's loan count"""
    _inherit = "res.partner"

    def _compute_partner_loans(self):
        """This compute the loan amount and total loans count of a partner."""
        self.loan_count = self.env['loan.request'].search_count(
            [('partner_id', '=', self.id),
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
            'view_mode': 'tree',
            'res_model': 'loan.request',
            'domain': [('partner_id', '=', self.id)],
            'context': "{'create': False}"
        }
