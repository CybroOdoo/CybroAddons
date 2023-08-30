# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
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


class ResPartner(models.Model):
    """Inherits the model res.partner for display the total due amount
     for the customer"""
    _inherit = 'res.partner'

    due_amount = fields.Float(string="Due Amount", help="Total due amount",
                              compute='_compute_due_amount')

    def action_view_due_statements(self):
        """Function for showing the all invoices that not paid completely"""
        due_invoices = self.env['account.move'].search(
            [('partner_id', '=', self.id), ('payment_state', '!=', 'paid'),
             ('move_type', '=', 'out_invoice')]).invoice_line_ids.mapped('id')
        return {
            'res_model': 'account.move.line',
            'type': 'ir.actions.act_window',
            'name': 'Due Statements',
            'view_mode': 'tree,form',
            'views':
                [(self.env.ref('multiple_payment_for_outstanding_dues'
                               '.account_move_line_view_tree').id,
                  'list'),
                 (self.env.ref('account.view_move_line_form').id, 'form')],
            'context': {'create': False,
                        'search_default_group_by_invoices': True},
            'domain': [('id', 'in', due_invoices)],
        }

    def _compute_due_amount(self):
        """Function for computing the total payment due of the customer"""
        self.due_amount = sum(self.env['account.move'].search(
            [('partner_id', '=', self.id), ('payment_state', '!=', 'paid'),
             ('move_type', '=', 'out_invoice')]).mapped('amount_residual'))
