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
import json
import re
from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError
from odoo.http import request


class AccountBankStatementLine(models.Model):
    """Update the 'rowdata' field for the specified record."""
    _name = 'account.bank.statement.line'
    _inherit = ['account.bank.statement.line', 'mail.thread',
                'mail.activity.mixin', 'analytic.mixin']

    lines_widget = fields.Char(string="Lines Widget")
    account_id = fields.Many2one('account.account', string='Account')
    tax_ids = fields.Many2many('account.tax', string='Taxes')
    form_name = fields.Char()
    form_balance = fields.Monetary(currency_field='currency_id')
    rowdata = fields.Json(string="RowData")
    matchRowdata = fields.Json(string="MatchRowData")
    record_id = fields.Integer()
    company_currency_id = fields.Many2one(
        related='company_id.currency_id', readonly=True,
    )
    bank_state = fields.Selection(selection=[('invalid', 'Invalid'),
                                             ('valid', 'Valid'),
                                             ('reconciled', 'Reconciled')],
                                  compute='_compute_state', store=True)
    reconcile_models_widget = fields.Char()
    lines_widget_json = fields.Json(store=True)
    has_matching_lines = fields.Boolean(
        string="Has Matching Lines",
        compute='_compute_has_matching_lines',
    )
    matched_reconcile_model_id = fields.Many2one(
        'account.reconcile.model',
        string="Matched Reconcile Model",
        compute='_compute_matched_reconcile_model',
    )
    matched_reconcile_model_name = fields.Char(
        string="Matched Reconcile Model Name",
        related='matched_reconcile_model_id.name',
        readonly=True,
    )
    reconciled_info_badge = fields.Char(
        string="Reconciled Information",
        compute='_compute_reconciled_info_badge',
    )

    @api.depends('payment_ref', 'narration', 'amount', 'partner_id', 'journal_id', 'is_reconciled')
    def _compute_matched_reconcile_model(self):
        for line in self:
            if line.is_reconciled:
                line.matched_reconcile_model_id = False
                continue
            models = self.env['account.reconcile.model'].search([
                ('company_id', 'in', (line.company_id.id, False)),
                ('trigger', '=', 'manual'),
            ])
            matched = False
            for model in models:
                if not model.line_ids.filtered(lambda l: l.account_id):
                    continue
                if line._reconcile_model_matches(model):
                    matched = model
                    break
            line.matched_reconcile_model_id = matched

    @api.depends('partner_id', 'company_id', 'is_reconciled')
    def _compute_has_matching_lines(self):
        for record in self:
            if record.is_reconciled or not record.partner_id:
                record.has_matching_lines = False
                continue
            partner = record.partner_id.commercial_partner_id
            count = self.env['account.move.line'].search_count([
                ('partner_id', '=', partner.id),
                ('account_id.reconcile', '=', True),
                ('parent_state', '=', 'posted'),
                ('reconciled', '=', False),
                ('company_id', '=', record.company_id.id),
            ], limit=1)
            record.has_matching_lines = bool(count)

    @api.depends('is_reconciled', 'move_id.line_ids.matched_debit_ids', 'move_id.line_ids.matched_credit_ids', 'move_id.line_ids.account_id')
    def _compute_reconciled_info_badge(self):
        for line in self:
            if not line.is_reconciled:
                line.reconciled_info_badge = False
                continue

            _liquidity, _suspense, other_lines = line._seek_for_lines()
            if not other_lines:
                other_lines = line.move_id.line_ids.filtered(
                    lambda l: l.account_id != line.journal_id.default_account_id
                )

            counterpart_amls = (
                other_lines.matched_debit_ids.debit_move_id |
                other_lines.matched_credit_ids.credit_move_id
            ) - other_lines

            matched_moves = (counterpart_amls.move_id - line.move_id).filtered(
                lambda m: m.name and m.name != '/'
            )
            if matched_moves:
                seen = set()
                inv_names = []
                for m in matched_moves:
                    if m.name not in seen:
                        seen.add(m.name)
                        inv_names.append(m.name)
                line.reconciled_info_badge = ', '.join(inv_names)
                continue

            accounts = other_lines.account_id
            if not accounts and line.account_id:
                accounts = line.account_id
            if accounts:
                line.reconciled_info_badge = ', '.join(accounts.mapped('name')) or accounts[:1].display_name
            else:
                line.reconciled_info_badge = _("Matched")

    @api.model
    def update_rowdata(self, record_id):
        """Update the 'rowdata' field for the specified record."""
        request.session['record_id'] = record_id

    @api.model
    def update_match_row_data(self, resId):
        """Update the match row data for a specific record identified by the given resId."""
        request.session['resId'] = resId
        move_record = self.env['account.move.line'].browse(resId)
        move_record_values = {
            'id': move_record.id,
            'account_id': move_record.account_id.id,
            'account_name': move_record.account_id.name,
            'account_code': move_record.account_id.code,
            'partner_id': move_record.partner_id,
            'partner_name': move_record.partner_id.name,
            'date': move_record.date,
            'move_id': move_record.move_id,
            'move_name': move_record.move_id.name,
            'name': move_record.name,
            'amount_residual_currency': move_record.amount_residual_currency,
            'amount_residual': move_record.amount_residual,
            'currency_id': move_record.currency_id.id,
            'currency_symbol': move_record.currency_id.symbol
        }
        return move_record_values

    def _get_selected_counterpart_aml(self):
        """Return the journal item(s) the user picked in the reconcile widget
        (persisted as JSON in ``lines_widget_json``), if any."""
        self.ensure_one()
        if not self.lines_widget_json:
            return self.env['account.move.line']
        try:
            data = json.loads(self.lines_widget_json)
        except (ValueError, TypeError):
            return self.env['account.move.line']
        if not isinstance(data, dict):
            return self.env['account.move.line']

        raw_ids = data.get('ids')
        if raw_ids is None and data.get('id'):
            raw_ids = [data.get('id')]
        if not raw_ids:
            return self.env['account.move.line']
        if isinstance(raw_ids, (int, str)):
            raw_ids = [raw_ids]
        aml_ids = []
        for i in raw_ids:
            try:
                aml_ids.append(int(i))
            except (ValueError, TypeError):
                continue
        if not aml_ids:
            return self.env['account.move.line']
        return self.env['account.move.line'].browse(aml_ids).exists()

    def _reconcile_with(self, counterpart_account, target_aml=None):
        """Assign ``counterpart_account`` to the suspense line and, when a
        reconcilable ``target_aml`` is given, reconcile the two. Standard v19
        primitives only — ``is_reconciled`` recomputes automatically."""
        self.ensure_one()
        _liquidity, suspense_lines, _other = self._seek_for_lines()
        counterpart_vals = self._prepare_move_line_default_vals(
            counterpart_account_id=counterpart_account.id)[1]
        if suspense_lines:
            command = Command.update(suspense_lines.id, counterpart_vals)
        else:
            command = Command.create(counterpart_vals)
        self.move_id.with_context(skip_readonly_check=True).write(
            {'line_ids': [command]})
        if target_aml and counterpart_account.reconcile:
            new_counterpart = self.move_id.line_ids.filtered(
                lambda l: l.account_id == counterpart_account
                and not l.reconciled)
            (new_counterpart | target_aml).filtered(
                lambda l: not l.reconciled).reconcile()

    def button_reconcile(self):
        """Reconcile action for Kanban card:
        If counterpart lines are explicitly selected in the widget, reconcile immediately.
        Otherwise, open the 'Search: Journal Items to Match' pop-up list view."""
        self.ensure_one()
        if self.is_reconciled:
            return {'type': 'ir.actions.client', 'tag': 'reload'}

        target_aml = self._get_selected_counterpart_aml()

        if target_aml:
            counterpart_account = target_aml[:1].account_id
            self._reconcile_with(counterpart_account, target_aml=target_aml)
            return {'type': 'ir.actions.client', 'tag': 'reload'}

        domain = [
            ('parent_state', '=', 'posted'),
            ('reconciled', '=', False),
            ('account_id.reconcile', '=', True),
            ('company_id', '=', self.company_id.id),
        ]
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.commercial_partner_id.id))

        return {
            'name': _("Search: Journal Items to Match"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'list',
            'views': [(self.env.ref('base_accounting_kit.view_aml_bank_rec_select_tree').id, 'list')],
            'target': 'new',
            'domain': domain,
            'context': {
                'active_st_line_id': self.id,
            },
        }

    def action_select_aml_to_reconcile(self, aml_id):
        """Reconcile this statement line with the selected account.move.line(s)."""
        self.ensure_one()
        aml = self.env['account.move.line'].browse(aml_id)
        if not aml.exists():
            return
        counterpart_account = aml[:1].account_id
        self._reconcile_with(counterpart_account, target_aml=aml)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def button_reconcile_partner_account(self):
        """Reconcile directly with the partner's default Receivable (if amount > 0)
        or Payable (if amount < 0) account."""
        self.ensure_one()
        if self.is_reconciled:
            return {'type': 'ir.actions.client', 'tag': 'reload'}
        if not self.partner_id:
            raise UserError(_("Please set a partner first."))

        partner = self.partner_id.commercial_partner_id
        if self.amount > 0:
            account = partner.property_account_receivable_id
        else:
            account = partner.property_account_payable_id

        if not account:
            account_type_label = _("Receivable") if self.amount > 0 else _("Payable")
            raise UserError(_("No default %s account found for partner %s.") % (account_type_label, partner.name))

        self._reconcile_with(account)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def button_set_partner(self):
        """Open the interactive list view of Partners for selecting a partner."""
        self.ensure_one()
        return {
            'name': _("Select Partner"),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'list',
            'views': [(self.env.ref('base_accounting_kit.view_partner_bank_rec_select_tree').id, 'list')],
            'target': 'new',
            'context': {
                'active_st_line_id': self.id,
            },
        }

    def action_set_partner(self, partner_id):
        """Assign partner to statement line and its move."""
        self.ensure_one()
        partner = self.env['res.partner'].browse(partner_id)
        if not partner.exists():
            return
        self.write({'partner_id': partner.id})
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def button_set_account(self):
        """Open the interactive list view of Chart of Accounts for selecting a counterpart account."""
        self.ensure_one()
        return {
            'name': _("Select Account"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.account',
            'view_mode': 'list',
            'views': [(self.env.ref('base_accounting_kit.view_account_bank_rec_select_tree').id, 'list')],
            'target': 'new',
            'context': {
                'active_st_line_id': self.id,
            },
        }

    def action_set_account(self, account_id):
        """Set counterpart account and reconcile directly."""
        self.ensure_one()
        account = self.env['account.account'].browse(account_id)
        if not account.exists():
            return
        self._reconcile_with(account)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_apply_reconcile_model(self, model_id=None):
        """Apply a manual reconciliation model to this statement line."""
        self.ensure_one()
        model = self.env['account.reconcile.model'].browse(model_id) if model_id else self.matched_reconcile_model_id
        if not model or not model.exists():
            return
        account = model.line_ids.filtered(lambda l: l.account_id)[:1].account_id
        if not account:
            return
        self._reconcile_with(account)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def button_validation(self, async_action=False):
        """Reconcile the statement line with the counterpart the user chose in
        the widget (a matched entry or an account)."""
        self.ensure_one()
        if self.is_reconciled:
            return {'type': 'ir.actions.client', 'tag': 'reload'}
        target_aml = self._get_selected_counterpart_aml()
        counterpart_account = target_aml[:1].account_id or self.account_id
        if not counterpart_account:
            raise UserError(_(
                "Select an account or an existing entry to reconcile with."))
        self._reconcile_with(counterpart_account, target_aml=target_aml)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    # ------------------------------------------------------------------
    # Auto-matching (Phase 3 #4)
    # ------------------------------------------------------------------
    def _reconcile_model_matches(self, model):
        """Whether the given reconcile model's conditions match this line."""
        self.ensure_one()
        # Require at least one matching condition
        if not (model.match_journal_ids or model.match_partner_ids or model.match_amount or (model.match_label and model.match_label_param)):
            return False
        if model.match_journal_ids and self.journal_id not in model.match_journal_ids:
            return False
        if model.match_partner_ids and \
                self.partner_id.commercial_partner_id not in model.match_partner_ids:
            return False
        amount = abs(self.amount)
        if model.match_amount == 'lower' and amount > model.match_amount_max:
            return False
        if model.match_amount == 'greater' and amount < model.match_amount_min:
            return False
        if model.match_amount == 'between' and not (
                model.match_amount_min <= amount <= model.match_amount_max):
            return False
        if model.match_label and model.match_label_param:
            label = ('%s %s' % (self.payment_ref or '',
                                self.narration or '')).lower()
            param = model.match_label_param.lower()
            if model.match_label == 'contains' and param not in label:
                return False
            if model.match_label == 'not_contains' and param in label:
                return False
            if model.match_label == 'match_regex':
                try:
                    if not re.search(model.match_label_param, label, re.I):
                        return False
                except re.error:
                    return False
        return True

    def _match_reconcile_model(self):
        """Return the write-off account proposed by the first matching
        ``account.reconcile.model`` rule, if any."""
        self.ensure_one()
        models = self.env['account.reconcile.model'].search(
            [('company_id', 'in', (self.company_id.id, False))])
        for model in models:
            if not model.line_ids.filtered(lambda l: l.account_id):
                continue
            if self._reconcile_model_matches(model):
                return model.line_ids.filtered(lambda l: l.account_id)[0].account_id
        return self.env['account.account']

    def _get_reconcile_proposal(self):
        """Propose a counterpart for auto-reconciliation:
        a unique open move line matching the partner + amount, else a
        reconcile-model write-off account. Returns a dict or {}."""
        self.ensure_one()
        partner = self.partner_id.commercial_partner_id
        if partner and not self.currency_id.is_zero(self.amount):
            candidates = self.env['account.move.line'].search([
                ('partner_id', '=', partner.id),
                ('account_id.reconcile', '=', True),
                ('parent_state', '=', 'posted'),
                ('reconciled', '=', False),
                ('company_id', '=', self.company_id.id),
                ('move_id.statement_line_id', '=', False),
            ])
            matches = candidates.filtered(
                lambda l: self.currency_id.compare_amounts(
                    abs(l.amount_residual), abs(self.amount)) == 0)
            if len(matches) == 1:
                return {'move_line': matches}
        account = self._match_reconcile_model()
        if account:
            return {'account': account}
        return {}

    def _auto_reconcile(self):
        """Auto-reconcile each line for which a unique proposal is found.
        Returns the lines that were reconciled."""
        done = self.env['account.bank.statement.line']
        for line in self.filtered(lambda l: not l.is_reconciled):
            proposal = line._get_reconcile_proposal()
            if proposal.get('move_line'):
                target = proposal['move_line']
                line._reconcile_with(target.account_id, target_aml=target)
                done |= line
            elif proposal.get('account'):
                line._reconcile_with(proposal['account'])
                done |= line
        return done

    def action_auto_reconcile(self):
        """Batch button / action: auto-reconcile the selected statement lines
        (or those in context)."""
        lines = self or self.browse(self.env.context.get('active_ids', []))
        lines._auto_reconcile()
        return True

    @api.model
    def _cron_auto_reconcile(self):
        """Scheduled action: auto-reconcile all unreconciled statement lines."""
        lines = self.search([('is_reconciled', '=', False),
                             ('move_id.state', '=', 'posted')])
        lines._auto_reconcile()

    def button_reset(self):
        """Reset the current bank statement line if it is in a 'reconciled' state."""
        self.ensure_one()
        if self.bank_state == 'reconciled':
            self.action_undo_reconciliation()
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

    def button_to_check(self, async_action=True):
        """Ensure the current recordset holds a single record, validate the bank
        state, and mark the move as 'to check'."""
        self.ensure_one()
        if self.bank_state == 'valid':
            self.button_validation(async_action=async_action)
            self.move_id.to_check = True
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

    def button_set_as_checked(self):
        """Mark the associated move as 'not to check' by setting 'to_check' to False."""
        self.ensure_one()
        self.move_id.to_check = False
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.model
    def get_statement_line(self, record_id):
        """Retrieve and format bank statement line details based on the provided record ID."""
        statement_line_records = self.env[
            'account.bank.statement.line'].search_read([('id', '=', record_id)])
        result_list = []
        for record in statement_line_records:
            move_id = record.get('move_id', False)
            partner_id = record.get('partner_id', False)
            date = record.get('date', False)
            amount = record.get('amount', False)
            currency_id = record.get('currency_id', False)
            payment_ref = record.get("payment_ref", False)
            bank_state = record.get("bank_state", False)
            id = record.get("id", False)
            if move_id:
                move_record = self.env['account.move.line'].search(
                    [('move_id', '=', move_id[0])], limit=1)
                currency_symbol = self.env['res.currency'].browse(
                    currency_id[0])
                account_id = move_record.account_id
                date_str = date.strftime('%Y-%m-%d') if date else None
                result_list.append({
                    'id': id,
                    'move_id': move_id,
                    'partner_id': partner_id,
                    'account_id': account_id.id,
                    'account_name': account_id.name,
                    'account_code': account_id.code,
                    'date': date_str,
                    'amount': amount,
                    'currency_symbol': currency_symbol.symbol,
                    'payment_ref': payment_ref,
                    'bank_state': bank_state,
                })
                # Update the account_id for the current record
                self.env['account.bank.statement.line'].browse(
                    record['id']).write({'account_id': account_id.id})
        return result_list

    @api.depends('account_id', 'is_reconciled')
    def _compute_state(self):
        """Compute the state of bank transactions based on the account's
         reconciliation status and journal settings."""
        for record in self:
            if record.is_reconciled:
                record.bank_state = 'reconciled'
            else:
                suspense_account = record.journal_id.suspense_account_id
                if suspense_account and record.account_id == suspense_account:
                    record.bank_state = 'invalid'
                else:
                    record.bank_state = 'valid'
