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
    """Inherits the model res.partner for display the total due amount
     for the customer"""
    _inherit = 'res.partner'

    due_amount = fields.Monetary(help="Total due amount of the customer in "
                                      "the company currency",
                                 currency_field='currency_id',
                                 compute='_compute_due_amount')

    def action_view_due_statements(self):
        """Function for showing all invoices that are not paid completely"""
        self.ensure_one()
        return {
            'res_model': 'account.move.line',
            'type': 'ir.actions.act_window',
            'name': self.env._('Due Statements'),
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('multiple_payment_for_outstanding_dues'
                              '.account_move_line_view_tree').id,
                 'list'),
                (self.env.ref('account.view_move_line_form').id, 'form'),
            ],
            'context': {
                'create': False,
                'search_default_group_by_invoices': True,
            },
            'domain': [
                ('move_id.partner_id', '=', self.id),
                ('move_id.move_type', '=', 'out_invoice'),
                ('move_id.state', '=', 'posted'),
                ('move_id.payment_state', 'not in', ('paid', 'in_payment', 'reversed')),
                ('display_type', 'in', ('product', 'line_section', 'line_subsection', 'line_note')),
            ],
        }

    def _compute_due_amount(self):
        """Function for computing the total payment due of the customer"""
        for partner in self:
            partner.due_amount = sum(self.env['account.move'].search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'posted'),
                ('payment_state', 'not in', ('paid', 'in_payment', 'reversed')),
                ('move_type', '=', 'out_invoice'),
            ]).mapped('amount_residual_signed'))

