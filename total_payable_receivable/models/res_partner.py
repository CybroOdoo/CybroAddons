# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class ResPartner(models.Model):
    """Inheriting res_partner model"""
    _name = 'res.partner'
    _inherit = 'res.partner'

    partner_credit = fields.Monetary(compute='_compute_partner_credit',
                                     string='Total Receivable',
                                     help="Total amount this customer owes you."
                                     )
    partner_debit = fields.Monetary(compute='_compute_partner_credit',
                                    string='Total Payable',
                                    help="Total amount you have to pay to this "
                                         "vendor.")

    @api.depends_context('company')
    def _compute_partner_credit(self):
        """
          Retrieve the total receivable and payable amounts from customers
          for the current company.
        """
        tables, where_clause, where_params = (
            self.env['account.move.line']._where_calc(
                [('parent_state', '=', 'posted'),
                 ('company_id', '=', self.env.company.id)]).get_sql())
        where_params = [tuple(self.ids)] + where_params
        if where_clause:
            where_clause = 'AND ' + where_clause
        self._cr.execute("""SELECT account_move_line.partner_id, a.account_type, 
                      SUM(account_move_line.amount_residual)
                      FROM """ + tables + """
                      LEFT JOIN account_account a ON 
                      (account_move_line.account_id=a.id)
                      WHERE a.account_type IN 
                      ('asset_receivable','liability_payable')
                      AND account_move_line.partner_id IN %s
                      AND account_move_line.reconciled IS FALSE
                      """ + where_clause + """
                      GROUP BY account_move_line.partner_id, a.account_type
                      """, where_params)
        treated = self.browse()
        query = self.env.cr.dictfetchall()
        for rec in query:
            partner = self.browse(rec['partner_id'])
            if rec['account_type'] == 'asset_receivable':
                self.partner_credit = rec['sum']
                if not self.partner_debit:
                    self.partner_debit = False
                treated |= partner
            elif rec['account_type'] == 'liability_payable':
                self.partner_debit = -rec['sum']
                if not self.partner_credit:
                    self.partner_credit = False
                treated |= partner
        remaining = (self - treated)
        remaining.partner_debit = False
        remaining.partner_credit = False
