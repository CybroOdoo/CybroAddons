# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _


class AccountJournal(models.Model):
    """Module inherited for adding the reconcile method in the account
    journal"""
    _inherit = "account.journal"

    @api.model_create_multi
    def create(self, vals_list):
        """Make the PDC payment method available on newly created bank
        journals. (Bank journals that already exist when the module is
        installed are linked automatically by the core
        ``_auto_link_payment_methods`` when the PDC method record is created.)"""
        journals = super().create(vals_list)
        bank_journals = journals.filtered(lambda j: j.type == 'bank')
        if bank_journals:
            methods = self.env['account.payment.method'].search(
                [('code', '=', 'pdc')])
            Line = self.env['account.payment.method.line']
            for method in methods:
                for journal in bank_journals:
                    if not Line.search_count([
                            ('payment_method_id', '=', method.id),
                            ('journal_id', '=', journal.id)]):
                        Line.create({
                            'name': method.name,
                            'payment_method_id': method.id,
                            'journal_id': journal.id,
                        })
        return journals

    multiple_invoice_ids = fields.One2many('multiple.invoice',
                                           'journal_id',
                                           string='Multiple Invoice')
    multiple_invoice_type = fields.Selection(
        [('text', 'Text'), ('watermark', 'Watermark')], required=True,
        default='text', string="Display Type")
    text_position = fields.Selection([
        ('header', 'Header'),
        ('footer', 'Footer'),
        ('body', 'Document Body')
    ], required=True, default='header', string='Text Position')
    body_text_position = fields.Selection([
        ('tl', 'Top Left'),
        ('tr', 'Top Right'),
        ('bl', 'Bottom Left'),
        ('br', 'Bottom Right'),
    ], default='tl', string='Body Text Position')
    text_align = fields.Selection([
        ('right', 'Right'),
        ('left', 'Left'),
        ('center', 'Center'),
    ], default='right', string='Center Align Text Position')
    layout = fields.Char(string="Layout",
                         related="company_id.external_report_layout_id.key")

    def action_open_reconcile(self):
        """Open the reconciliation view based on the type of the account journal."""
        self.ensure_one()
        if self.type in ('bank', 'cash'):
            views = [
                (self.env.ref(
                    'base_accounting_kit.account_bank_statement_line_view_kanban').id,
                 'kanban'),
                (self.env.ref(
                    'base_accounting_kit.account_bank_statement_line_view_tree').id,
                 'list'),  # Include tree view
            ]
            context = {
                'default_journal_id': self.id,
                'search_default_journal_id': self.id,
            }
            kanban_first = True
            name = None
            extra_domain = None
            return {
                'name': name or _("Bank Reconciliation"),
                'type': 'ir.actions.act_window',
                'res_model': 'account.bank.statement.line',
                'context': context,
                'search_view_id': [
                    self.env.ref(
                        'base_accounting_kit.account_bank_statement_line_view_search').id,
                    'search'],
                'view_mode': 'kanban,list' if kanban_first else 'list,kanban',
                'views': views if kanban_first else views[::-1],
                'domain': [('state', '!=', 'cancel')] + (extra_domain or []),
                'help': _("""
                            <p class="o_view_nocontent_smiling_face">
                                Nothing to do here!
                            </p>
                            <p>
                                No transactions matching your filters were found.
                            </p>
                        """),
            }
        else:
            # Open the customer/supplier open items for manual reconciliation.
            # (The enterprise 'manual_reconciliation_view' client action is not
            # available in Community, so we open the reconcilable journal items.)
            account_type = ('asset_receivable' if self.type == 'sale'
                            else 'liability_payable')
            return {
                'name': _("Reconciliation"),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move.line',
                'view_mode': 'list,form',
                'domain': [
                    ('account_id.account_type', '=', account_type),
                    ('parent_state', '=', 'posted'),
                    ('reconciled', '=', False),
                    ('company_id', 'in', self.mapped('company_id').ids),
                ],
                'context': {'search_default_group_by_partner': 1},
            }

    def action_import_wizard(self):
        """Function to open wizard"""
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'import.bank.statement',
            'target': 'new',
            'context': {
                'default_journal_id': self.id,
            }
        }
