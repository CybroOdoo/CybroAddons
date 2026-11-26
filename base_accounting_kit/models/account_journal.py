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
from odoo import Command, api, fields, models, _


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
        if self.type in ('bank', 'cash', 'credit'):
            # The kit's reconciliation screen (client action), on this journal.
            action = self.env['ir.actions.actions']._for_xml_id(
                'base_accounting_kit.action_kit_bank_reconciliation')
            action['params'] = {'journal_id': self.id}
            return action
        # Sale / purchase journals: the Open Items mode on their account type.
        action = self.env['ir.actions.actions']._for_xml_id('base_accounting_kit.action_kit_open_items')
        action['params'] = {'mode': 'open', 'account_type': 'receivable' if self.type == 'sale' else 'payable'}
        return action

    kit_import_map_ids = fields.One2many(
        'kit.statement.import.map', 'journal_id', string="Import Formats",
        help="Saved CSV / XLSX formats of this journal's bank files.")

    def _get_bank_statements_available_sources(self):
        """Statements imported from bank files (CAMT, MT940, CSV, XLSX, OFX,
        QIF) with the kit's import."""
        return super()._get_bank_statements_available_sources() + [
            ('kit_file_import', _("File Import"))]

    def _import_bank_statement(self, attachments):
        """Import statement files into this journal. Core calls it for files
        sent by email to the journal's alias (``message_new``); returns an
        action whose domain gives the new statement lines."""
        self.ensure_one()
        wizard = self.env['import.bank.statement'].create({
            'journal_id': self.id,
            'attachment_ids': [Command.set(attachments.ids)],
        })
        statements, _summary, _skipped = wizard._import_files()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Imported Transactions"),
            'res_model': 'account.bank.statement.line',
            'domain': [('statement_id', 'in', statements.ids)],
            'views': [(False, 'list'), (False, 'form')],
        }

    def action_import_wizard(self):
        """Open the statement import for this journal."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Import Statement'),
            'view_mode': 'form',
            'res_model': 'import.bank.statement',
            'target': 'new',
            'context': {
                'default_journal_id': self.id,
            }
        }
