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
import logging
import re
from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError
from odoo.fields import Domain
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)


class AccountBankStatementLine(models.Model):
    """Bank transactions: manual operations, reconcile models, the matching
    engine and the server side of the reconciliation screen."""
    _name = 'account.bank.statement.line'
    _inherit = ['account.bank.statement.line', 'mail.thread',
                'mail.activity.mixin', 'analytic.mixin']

    account_id = fields.Many2one('account.account', string='Account')
    tax_ids = fields.Many2many('account.tax', string='Taxes')
    kit_import_id = fields.Char(
        string='Import Key', readonly=True, copy=False,
        index='btree_not_null',
        help="Set when the line comes from a statement file import; used to "
             "skip the transactions already imported.")
    company_currency_id = fields.Many2one(
        related='company_id.currency_id', readonly=True,
    )
    matched_reconcile_model_id = fields.Many2one(
        'account.reconcile.model',
        string="Matched Reconcile Model",
        compute='_compute_matched_reconcile_model',
    )
    # Computed with the model (a related field on a non-stored compute
    # cannot be tracked by Odoo).
    matched_reconcile_model_name = fields.Char(
        string="Matched Reconcile Model Name",
        compute='_compute_matched_reconcile_model',
    )
    reconciled_info_badge = fields.Char(
        string="Reconciled Information",
        compute='_compute_reconciled_info_badge',
    )

    @api.depends('payment_ref', 'narration', 'amount', 'partner_id', 'journal_id', 'is_reconciled')
    def _compute_matched_reconcile_model(self):
        models_by_company = {}
        for line in self:
            matched = self.env['account.reconcile.model']
            if not line.is_reconciled:
                company = line.company_id.id
                if company not in models_by_company:
                    models_by_company[company] = line._reconcile_models('manual')
                matched = next((model for model in models_by_company[company]
                                if line._reconcile_model_matches(model)), matched)
            line.matched_reconcile_model_id = matched
            line.matched_reconcile_model_name = matched.name

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

    # ------------------------------------------------------------------
    # Write-off lines (manual operations and reconcile models)
    # ------------------------------------------------------------------
    def _transaction_amounts(self):
        """Amount of the statement line in its transaction currency and in
        the company currency, as core books them
        (``_prepare_move_line_default_vals``)."""
        self.ensure_one()
        counterpart = self._prepare_move_line_default_vals()[1]
        currency = self.env['res.currency'].browse(counterpart['currency_id'])
        transaction = -counterpart['amount_currency']
        company = counterpart['credit'] - counterpart['debit']
        return currency, transaction, company

    def _writeoff_lines_vals(self, parts):
        """Journal item values for write-off parts.

        :param parts: list of dicts ``account`` (account.account),
            ``amount`` (counterpart amount in transaction currency, signed:
            negative = credit), ``taxes``, ``analytic_distribution``,
            ``label``. The amount includes the taxes: it is split into a base
            line and one line per tax with core's ``compute_all`` and
            ``force_price_include`` (``account_tax.py``).
        :return: list of values in transaction currency (``amount_currency``)
        """
        self.ensure_one()
        currency, _transaction, _company = self._transaction_amounts()
        vals_list = []
        for part in parts:
            amount = currency.round(part['amount'])
            if currency.is_zero(amount):
                continue
            label = part.get('label') or self.payment_ref
            taxes = part.get('taxes') or self.env['account.tax']
            partner = part.get('partner') or self.partner_id
            base = {
                'name': label,
                'account_id': part['account'].id,
                'partner_id': partner.id,
                'currency_id': currency.id,
                'analytic_distribution': part.get('analytic_distribution')
                or False,
                'reconcile_model_id': part['model'].id if part.get('model')
                else False,
            }
            if not taxes:
                vals_list.append(dict(base, amount_currency=amount))
                continue
            sign = -1 if amount < 0 else 1
            # Money in on a purchase tax (or out on a sale tax) is a refund.
            is_refund = (sign < 0) == (taxes[:1].type_tax_use == 'purchase')
            res = taxes.with_context(force_price_include=True).compute_all(
                abs(amount), currency=currency, partner=self.partner_id,
                is_refund=is_refund)
            vals_list.append(dict(
                base, amount_currency=sign * res['total_excluded'],
                tax_ids=[(6, 0, taxes.ids)],
                tax_tag_ids=[(6, 0, res['base_tags'])]))
            for tax in res['taxes']:
                vals_list.append({
                    'name': tax['name'],
                    'account_id': tax['account_id'] or part['account'].id,
                    'partner_id': partner.id,
                    'reconcile_model_id': base['reconcile_model_id'],
                    'currency_id': currency.id,
                    'amount_currency': sign * tax['amount'],
                    'tax_repartition_line_id': tax['tax_repartition_line_id'],
                    'tax_tag_ids': [(6, 0, tax['tag_ids'])],
                    'analytic_distribution': base['analytic_distribution']
                    if tax['analytic'] else False,
                })
        return vals_list

    def _replace_counterpart(self, vals_list):
        """Replace the suspense line by ``vals_list``; what they don't cover
        stays on the suspense account (the line remains to reconcile)."""
        liquidity, vals_list = self._counterpart_entry_vals(vals_list)
        # Rewrite the journal items as core does in
        # ``action_undo_reconciliation``: clear them and create the liquidity
        # line and the new counterpart lines.
        self.with_context(force_delete=True, skip_readonly_check=True).write({
            'line_ids': [Command.clear(), Command.create(liquidity)]
            + [Command.create(vals) for vals in vals_list],
        })

    def _counterpart_entry_vals(self, vals_list):
        """The bank entry lines for the counterparts ``vals_list`` (company
        amounts at the bank rate, the rest on suspense), without writing.

        :return: (liquidity line values, counterpart line values)
        """
        self.ensure_one()
        currency, transaction, company_amount = self._transaction_amounts()
        company_currency = self.company_id.currency_id
        rate = company_amount / transaction if transaction else 1.0
        total = 0.0
        for vals in vals_list:
            vals['balance'] = company_currency.round(
                vals['amount_currency'] * rate)
            total += vals['amount_currency']
        remaining = currency.round(-transaction - total)
        if not currency.is_zero(remaining):
            suspense = self._prepare_move_line_default_vals()[1]
            vals_list.append({
                'name': self.payment_ref,
                'account_id': suspense['account_id'],
                'partner_id': self.partner_id.id,
                'currency_id': currency.id,
                'amount_currency': remaining,
                'balance': 0.0,
            })
        # The company amounts must add up exactly to the bank amount.
        diff = company_currency.round(
            -company_amount - sum(v['balance'] for v in vals_list))
        if vals_list and not company_currency.is_zero(diff):
            vals_list[-1]['balance'] += diff
        liquidity = self._prepare_move_line_default_vals()[0]
        liquidity.pop('move_id', None)
        return liquidity, vals_list

    def _reconcile_model_parts(self, model, remaining=None):
        """Write-off parts of a reconcile model: each model line with an
        account, in order. Percentage = of the remaining amount, percentage
        of statement line = of the bank amount, fixed = that amount, from
        label = the amount read from the label with the line's regex.

        :param remaining: counterpart amount still to book (transaction
            currency, signed); the whole bank amount by default.
        """
        self.ensure_one()
        currency, transaction, _company = self._transaction_amounts()
        if remaining is None:
            remaining = -transaction
        parts = []
        for line in model.line_ids.filtered('account_id'):
            if line.amount_type == 'percentage':
                amount = remaining * line.amount / 100.0
            elif line.amount_type == 'percentage_st_line':
                amount = -transaction * line.amount / 100.0
            elif line.amount_type == 'fixed':
                # Core: a positive fixed amount is a credit, negative a debit.
                amount = -line.amount
            elif line.amount_type == 'regex':
                value = self._amount_from_label(line.amount_string)
                if value is None:
                    continue
                amount = value if remaining >= 0 else -value
            else:
                continue
            amount = currency.round(amount)
            parts.append({
                'account': line.account_id,
                'amount': amount,
                'taxes': line.tax_ids,
                'analytic_distribution': line.analytic_distribution,
                'label': line.label,
                'partner': line.partner_id,
                'model': model,
            })
            remaining -= amount
        return parts

    def _apply_manual_operation(self, account):
        """Book the whole amount on ``account`` with the taxes and analytic
        entered under Manual Operations."""
        self.ensure_one()
        _currency, transaction, _company = self._transaction_amounts()
        self._replace_counterpart(self._writeoff_lines_vals([{
            'account': account,
            'amount': -transaction,
            'taxes': self.tax_ids,
            'analytic_distribution': self.analytic_distribution,
        }]))

    def action_apply_reconcile_model(self, model_id=None):
        """Apply a manual reconciliation model to this statement line."""
        self.ensure_one()
        model = self.env['account.reconcile.model'].browse(model_id) if model_id else self.matched_reconcile_model_id
        if not model or not model.exists():
            return
        parts = self._reconcile_model_parts(model)
        if not parts:
            return
        self._replace_counterpart(self._writeoff_lines_vals(parts))
        self._schedule_model_activity(model)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def _schedule_model_activity(self, model):
        """Schedule the model's next activity on the bank entry."""
        activity_type = model.next_activity_type_id
        if activity_type:
            self.move_id.activity_schedule(
                activity_type_id=activity_type.id,
                user_id=activity_type.default_user_id.id or self.env.uid)

    def button_validation(self):
        """Manual operation: book the whole amount on ``account_id`` with
        the taxes and analytic entered on the transaction."""
        self.ensure_one()
        if self.is_reconciled:
            return True
        if not self.account_id:
            raise UserError(_("Select an account to book the transaction on."))
        self._apply_manual_operation(self.account_id)
        return True

    # ------------------------------------------------------------------
    # Auto-matching (Phase 3 #4)
    # ------------------------------------------------------------------
    def _reconcile_model_matches(self, model, require_condition=True):
        """Whether the given reconcile model's conditions match this line.
        A reconcile model needs at least one condition; a matching rule
        without condition applies to every line."""
        self.ensure_one()
        if require_condition and not (
                model.match_journal_ids or model.match_partner_ids
                or model.match_amount
                or (model.match_label and model.match_label_param)):
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

    def _reconcile_models(self, trigger):
        """Reconcile models (not matching rules) of the line's company with
        write-off lines and the given trigger ('manual' or
        'auto_reconcile')."""
        return self.env['account.reconcile.model'].search([
            ('company_id', 'in', (self.company_id.id, False)),
            ('trigger', '=', trigger),
            ('rule_type', '!=', 'matching_rule'),
        ]).filtered(lambda model: model.line_ids.filtered('account_id'))

    def _match_reconcile_model(self, trigger='auto_reconcile'):
        """Return the first matching reconcile model with write-off lines
        and the given trigger, if any."""
        self.ensure_one()
        return next((model for model in self._reconcile_models(trigger)
                     if self._reconcile_model_matches(model)),
                    self.env['account.reconcile.model'])

    def _label_text(self):
        """Label and notes of the transaction, as plain text."""
        return ' '.join(filter(None, (
            self.payment_ref, html2plaintext(self.narration or ''))))

    def _mentioned_in_label(self, lines):
        """The open items whose entry number or reference appears in the
        transaction label."""
        label = self._label_text().lower()

        def mentioned(line):
            move = line.move_id
            return any(ref and len(ref) >= 3 and ref.lower() in label
                       for ref in (move.name, move.ref, move.payment_reference))
        return lines.filtered(mentioned)

    def _amount_from_label(self, pattern):
        """Amount read from the label with a reconcile model line's regex
        (core's "From label"): one captured text is the amount, with ``,``
        or ``.`` as decimal separator; two captured texts are the units and
        the decimals. None when the label does not match."""
        try:
            found = re.search(pattern, self._label_text(), re.I)
        except re.error:
            return None
        if not found:
            return None
        captured = [text for text in found.groups() if text] or [found.group(0)]
        return self._kit_parse_amount(*captured[:2])

    @staticmethod
    def _kit_parse_amount(text, decimals=None):
        """Number written in ``text`` (thousands and decimal separators
        ``,`` / ``.``); with ``decimals``, ``text`` holds the units only."""
        digits = ''.join(char for char in text if char.isdigit())
        if decimals is not None:
            cents = ''.join(char for char in decimals if char.isdigit())
            number = '%s.%s' % (digits or '0', cents or '0')
        else:
            kept = ''.join(char for char in text if char.isdigit() or char in ',.')
            head, sep, tail = max(kept.rpartition(','), kept.rpartition('.'),
                                  key=lambda part: len(part[0]))
            # a separator followed by one or two digits marks the decimals
            if sep and 1 <= len(tail) <= 2 and tail.isdigit():
                number = '%s.%s' % (''.join(c for c in head if c.isdigit()) or '0', tail)
            else:
                number = digits
        try:
            return float(number)
        except ValueError:
            return None

    # ------------------------------------------------------------------
    # Matching engine (P2.1-b)
    # ------------------------------------------------------------------
    def _detect_partner(self):
        """Partner of a transaction without one: the owner of its bank
        account number, else the only partner with exactly its partner name,
        else a partner mapping reconcile model whose conditions match."""
        self.ensure_one()
        company = self.company_id
        if self.account_number:
            owners = self.env['res.partner.bank'].search([
                ('account_number', '=', self.account_number),
                ('company_id', 'in', (False, company.id)),
            ]).partner_id.commercial_partner_id
            if len(owners) == 1:
                return owners
        if self.partner_name:
            partners = self.env['res.partner'].search([
                ('name', '=ilike', self.partner_name.strip()),
                ('company_id', 'in', (False, company.id)),
            ]).commercial_partner_id
            if len(partners) == 1:
                return partners
        mappings = self.env['account.reconcile.model'].search([
            ('company_id', '=', company.id),
            ('mapped_partner_id', '!=', False),
        ])
        for model in mappings:
            if self._reconcile_model_matches(model):
                return model.mapped_partner_id.commercial_partner_id
        return self.env['res.partner']

    def _open_items(self, partner, cache):
        """Open items a transaction can be matched with (core's
        ``_get_default_amls_matching_domain``): the partner's, or without a
        partner the open receivables and payables. Searched once per
        company and partner in a batch (``cache``)."""
        key = ('items', self.company_id.id, partner.id)
        if key not in cache:
            # The last leaf excludes the line itself: filtered below so the
            # result can be shared by the lines of a batch.
            domain = [leaf for leaf in self._get_default_amls_matching_domain()
                      if not (isinstance(leaf, tuple) and leaf[0] == 'statement_line_id')]
            if partner:
                domain.append(('partner_id', 'child_of', partner.id))
            else:
                domain.append(('account_id.account_type', 'in',
                               ('asset_receivable', 'liability_payable')))
            cache[key] = self.env['account.move.line'].search(domain)
        return cache[key].filtered(lambda line: line.statement_line_id != self)

    def _open_residual(self, line, currency):
        """Open amount of an item in the transaction currency (signed), or
        None when it cannot be compared."""
        if line.currency_id == currency:
            return line.amount_residual_currency
        if currency == self.company_id.currency_id:
            return line.amount_residual
        return None

    @staticmethod
    def _sorted_items(lines, newest_first=False):
        """Oldest (or newest) first, by due date."""
        return lines.sorted(lambda line: (line.date_maturity or line.date, line.id),
                            reverse=newest_first)

    def _find_combination(self, items, target, currency, size=6, budget=20000):
        """Several items (2 to ``size``) whose open amounts add up to
        ``target``: depth-first search over the 50 oldest items, stopped
        after ``budget`` steps so it stays fast."""
        amounts = [(line, abs(residual)) for line, residual in items
                   if currency.compare_amounts(abs(residual), abs(target)) < 0][:50]
        goal = abs(target)
        steps = [0]

        def search(start, chosen, total):
            if len(chosen) >= 2 and currency.compare_amounts(total, goal) == 0:
                return chosen
            if len(chosen) == size or steps[0] > budget:
                return None
            for index in range(start, len(amounts)):
                steps[0] += 1
                line, amount = amounts[index]
                if currency.compare_amounts(total + amount, goal) > 0:
                    continue
                found = search(index + 1, chosen + [line], total + amount)
                if found:
                    return found
            return None
        found = search(0, [], 0.0)
        return self.env['account.move.line'].union(found) if found else None

    def _suggestions(self, cache=None, partner=None):
        """Ranked matching suggestions for the transaction.

        Each suggestion is a dict: ``lines`` (journal items), ``score``,
        ``reasons`` (texts), ``sure`` (safe to reconcile automatically).
        Points: same amount 40, reference in the label 40, same partner 15;
        several items that add up to the amount count as one suggestion.
        """
        self.ensure_one()
        cache = {} if cache is None else cache
        currency, transaction, _company = self._transaction_amounts()
        if currency.is_zero(transaction):
            return []
        if partner is None:
            partner = self.partner_id.commercial_partner_id
        sign = 1 if transaction > 0 else -1
        residuals = {}
        for line in self._open_items(partner, cache):
            residual = self._open_residual(line, currency)
            # Money in matches open debits, money out open credits.
            if residual is not None and currency.compare_amounts(residual * sign, 0) > 0:
                residuals[line] = residual
        pool = self._sorted_items(self.env['account.move.line'].union(residuals))
        named = self._mentioned_in_label(pool)
        suggestions = []
        for line in pool:
            score, reasons = 0, []
            same_amount = currency.compare_amounts(residuals[line], transaction) == 0
            discounted = self._discounted_residual(line, currency)
            early = not same_amount and discounted is not None \
                and currency.compare_amounts(discounted, transaction) == 0
            if same_amount or early:
                score += 40
                reasons.append(_("Same amount") if same_amount else _("Early payment discount"))
            if line in named:
                score += 40
                reasons.append(_("Reference in label"))
            if partner and line.partner_id.commercial_partner_id == partner:
                score += 15
                reasons.append(_("Same partner"))
            if score:
                suggestions.append({'lines': line, 'score': score, 'reasons': reasons,
                                    'same_amount': same_amount or early, 'discount': early, 'sure': False})
        exact = [s for s in suggestions if s['same_amount']]
        if partner and len(exact) == 1:
            exact[0]['sure'] = True
        elif not partner:
            exact_named = [s for s in exact if s['lines'] in named]
            if len(exact_named) == 1:
                exact_named[0]['sure'] = True
        # Several items that add up to the amount.
        total_named = sum(residuals[line] for line in named)
        if len(named) >= 2 and currency.compare_amounts(total_named, transaction) == 0:
            suggestions.append({
                'lines': named, 'score': 80 + (15 if partner else 0),
                'reasons': [_("References in label"), _("Add up to the amount")],
                'same_amount': True, 'sure': True})
        elif partner:
            combination = self._find_combination(
                [(line, residuals[line]) for line in pool], transaction, currency)
            if combination:
                suggestions.append({
                    'lines': combination, 'score': 55,
                    'reasons': [_("Add up to the amount"), _("Same partner")],
                    'same_amount': True, 'sure': False})
        suggestions.sort(key=lambda s: -s['score'])
        return suggestions

    def _discounted_residual(self, line, currency):
        """Open amount of an invoice item after core's early payment
        discount, when the transaction date still allows it, else None."""
        if line.display_type == 'payment_term' and line.currency_id == currency \
                and line.discount_amount_currency \
                and line.move_id._is_eligible_for_early_payment_discount(currency, self.date):
            return line.discount_amount_currency
        return None

    def _early_discount_vals(self, lines, open_amount):
        """Core's early payment discount lines (as Register Payment books
        them: cash discount gain/loss, taxes when the discount is computed
        tax included) for the eligible ``lines``, covering ``open_amount``
        (counterpart amount still to book, transaction currency)."""
        currency, transaction, company_amount = self._transaction_amounts()
        eligible = lines.filtered(
            lambda l: l.move_id._is_eligible_for_early_payment_discount(currency, self.date))
        if not eligible:
            return []
        rate = company_amount / transaction if transaction else 1.0
        values = self.env['account.move']._get_invoice_counterpart_amls_for_early_payment_discount(
            [{'aml': l, 'amount_currency': -l.amount_residual_currency, 'balance': -l.amount_residual}
             for l in eligible],
            self.company_id.currency_id.round(open_amount * rate))
        vals_list = []
        for group in values.values():
            for vals in group:
                vals_list.append(dict(vals, currency_id=vals.get('currency_id') or currency.id))
        return vals_list

    def _matching_rules(self, cache):
        """Core matching rules of the line's company (once per batch)."""
        key = ('rules', self.company_id.id)
        if key not in cache:
            cache[key] = self.env['account.reconcile.model'].search([
                ('company_id', '=', self.company_id.id),
                ('rule_type', '=', 'matching_rule'),
                ('trigger', '=', 'auto_reconcile'),
            ])
        return cache[key]

    def _apply_matching_rule(self, rule, partner, cache):
        """Proposal from a matching rule: the items named in the label, else
        the partner's items in the rule's order, until their total is within
        the rule's payment tolerance of the bank amount. The gap is booked
        with the rule's counterpart items; without counterpart account the
        last item stays partly open (or keeps the extra)."""
        currency, transaction, _company = self._transaction_amounts()
        sign = 1 if transaction > 0 else -1
        items = self.env['account.move.line']
        residuals = {}
        for line in self._open_items(partner, cache):
            residual = self._open_residual(line, currency)
            if residual is not None and currency.compare_amounts(residual * sign, 0) > 0:
                residuals[line] = residual
                items |= line
        candidates = self._mentioned_in_label(items) or (items if partner else items.browse())
        candidates = self._sorted_items(candidates, rule.matching_order == 'new_first')
        chosen, total = self.env['account.move.line'], 0.0
        for line in candidates:
            chosen |= line
            total += residuals[line]
            tolerance = rule.payment_tolerance if rule.payment_tolerance_type == 'amount' \
                else abs(total) * rule.payment_tolerance / 100.0
            gap = currency.round(total - transaction)
            if currency.compare_amounts(abs(gap), tolerance) <= 0:
                if currency.is_zero(gap):
                    return {'items': [(item, None) for item in chosen], 'rule': rule}
                parts = self._reconcile_model_parts(rule, remaining=gap)
                if parts:
                    return {'items': [(item, None) for item in chosen], 'parts': parts, 'rule': rule}
                others = chosen[:-1]
                last_amount = transaction - sum(residuals[item] for item in others)
                return {'items': [(item, None) for item in others] + [(chosen[-1], last_amount)],
                        'rule': rule}
            if currency.compare_amounts(abs(total), abs(transaction) + tolerance) > 0:
                return {}
        return {}

    def _get_reconcile_proposal(self, cache=None):
        """What auto-reconcile may book for this transaction, only when it
        is sure: a sure suggestion, else a matching rule within its
        tolerance, else an automatic reconcile model.

        :return: dict with ``items`` (list of (journal item, amount or None
            for its whole open amount)), ``parts`` (write-off parts),
            ``rule``, ``partner``; or ``model``; or {} when nothing is sure.
        """
        self.ensure_one()
        cache = {} if cache is None else cache
        partner = self.partner_id.commercial_partner_id or self._detect_partner()
        proposal = {}
        sure = next((s for s in self._suggestions(cache, partner) if s['sure']), None)
        if sure:
            proposal = {'items': [(line, None) for line in sure['lines']], 'reasons': sure['reasons'],
                        'discount': sure.get('discount', False)}
        else:
            for rule in self._matching_rules(cache):
                if self._reconcile_model_matches(rule, require_condition=False):
                    proposal = self._apply_matching_rule(rule, partner, cache)
                    if proposal:
                        proposal['reasons'] = [_("Matching rule: %s", rule.name)]
                        break
        if proposal:
            if not partner:
                partner = self.env['account.move.line'].union(
                    line for line, _amount in proposal['items']).partner_id.commercial_partner_id
            proposal['partner'] = partner if len(partner) == 1 else partner.browse()
            return proposal
        model = self._match_reconcile_model()
        if model:
            return {'model': model, 'partner': partner, 'reasons': [_("Automated model")]}
        return {'partner': partner} if partner else {}

    def _items_counterpart_vals(self, items, parts=(), discount=False):
        """Counterpart values for open items, write-off parts and, with
        ``discount``, the early payment discount of the items."""
        self.ensure_one()
        currency, transaction, _company = self._transaction_amounts()
        vals_list = []
        total = 0.0
        for line, amount in items:
            if amount is None:
                amount = self._open_residual(line, currency)
            total += amount
            vals_list.append({
                'name': self.payment_ref or line.name,
                'account_id': line.account_id.id,
                'partner_id': line.partner_id.id,
                'currency_id': currency.id,
                'amount_currency': -currency.round(amount),
            })
        writeoffs = self._writeoff_lines_vals(list(parts))
        vals_list += writeoffs
        if discount:
            booked = sum(vals['amount_currency'] for vals in writeoffs)
            open_amount = currency.round(total - transaction - booked)
            lines = self.env['account.move.line'].union(line for line, _amount in items)
            vals_list += self._early_discount_vals(lines, open_amount)
        return vals_list

    def _reconcile_items(self, items, parts=(), rule=None, discount=False):
        """Book the transaction against open items and write-off parts and
        reconcile the items; what is not covered stays on suspense.

        :param items: list of (journal item, amount): the amount in the
            transaction currency, signed like the item's open amount, or
            None for its whole open amount (a smaller amount reconciles it
            partially).
        :param parts: write-off parts (see ``_writeoff_lines_vals``).
        :param discount: book the difference as core's early payment
            discount of the items.
        """
        self.ensure_one()
        self._replace_counterpart(self._items_counterpart_vals(items, parts, discount))
        # Counterparts are created in order after the liquidity line.
        counterparts = self.move_id.line_ids.sorted('id')[1:1 + len(items)]
        for counterpart, (line, _amount) in zip(counterparts, items):
            (counterpart | line).reconcile()
        if rule:
            self._schedule_model_activity(rule)

    def _auto_reconcile(self):
        """Auto-reconcile each line for which a sure proposal is found,
        each in its own savepoint: a line that fails is logged and skipped.
        A partner found on the way is set on the line. Open items and rules
        are searched once per company and partner for the whole batch.
        Returns the lines that were reconciled."""
        done = self.env['account.bank.statement.line']
        cache = {}
        for line in self.filtered(lambda l: not l.is_reconciled):
            try:
                with self.env.cr.savepoint():
                    proposal = line._get_reconcile_proposal(cache)
                    if proposal.get('partner') and not line.partner_id:
                        line.partner_id = proposal['partner']
                    if proposal.get('items'):
                        line._reconcile_items(proposal['items'], proposal.get('parts', ()),
                                              proposal.get('rule'), proposal.get('discount', False))
                        done |= line
                    elif proposal.get('model'):
                        line.action_apply_reconcile_model(proposal['model'].id)
                        done |= line
            except Exception:  # noqa: BLE001 - one line must not stop the batch
                _logger.warning("Auto-reconcile skipped statement line %s",
                                line.id, exc_info=True)
        return done

    # ------------------------------------------------------------------
    # Reconciliation screen (P2.1-c): client action kit_bank_reconciliation
    # ------------------------------------------------------------------
    _KIT_REC_LIMIT = 200

    @api.model
    def _kit_rec_journals(self):
        """Bank, cash and credit card journals of the allowed companies."""
        return self.env['account.journal'].search([
            *self.env['account.journal']._check_company_domain(self.env.companies),
            ('type', 'in', ('bank', 'cash', 'credit')),
        ])

    def _kit_rec_to_check(self):
        return self.move_id.review_state in ('todo', 'anomaly')

    def _kit_rec_row(self, cache):
        """One row of the screen: the transaction, its group (sure /
        confirm / needs / check / done) and its best proposal."""
        self.ensure_one()
        row = {
            'id': self.id,
            'move_id': self.move_id.id,
            'date': fields.Date.to_string(self.date),
            'label': self.payment_ref or '',
            'partner': self.partner_id.display_name or '',
            'partner_found': '',
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'reconciled': self.is_reconciled,
            'to_check': self._kit_rec_to_check(),
            'proposal': '',
            'reasons': [],
        }
        if row['to_check']:
            row.update(group='check', proposal=self.reconciled_info_badge or '')
        elif self.is_reconciled:
            row.update(group='done', proposal=self.reconciled_info_badge or '')
        else:
            proposal = self._get_reconcile_proposal(cache)
            partner = proposal.get('partner') or self.env['res.partner']
            if partner and not self.partner_id:
                row['partner_found'] = partner.display_name
            if proposal.get('items'):
                names = [line.move_id.name for line, _amount in proposal['items']]
                row.update(group='sure', proposal=' + '.join(names), reasons=proposal.get('reasons', []))
            elif proposal.get('model'):
                row.update(group='sure', proposal=_("Model: %s", proposal['model'].name),
                           reasons=proposal.get('reasons', []))
            else:
                # Same amount alone (unknown payer) is too weak to propose.
                best = next((s for s in self._suggestions(cache, partner.commercial_partner_id)
                             if s['score'] >= 55), None)
                if best:
                    row.update(group='confirm', proposal=' + '.join(best['lines'].move_id.mapped('name')),
                               reasons=best['reasons'])
                elif self.matched_reconcile_model_id:
                    row.update(group='confirm', proposal=_("Model: %s", self.matched_reconcile_model_id.name),
                               reasons=[_("The model's conditions match")])
                else:
                    row['group'] = 'needs'
        return row

    @api.model
    def kit_rec_load(self, filters=None):
        """Rows of the reconciliation screen for a journal and a status
        (todo / check / done / all), searched by label, partner or amount."""
        filters = dict(filters or {})
        journals = self._kit_rec_journals()
        journal = journals.filtered(lambda j: j.id == filters.get('journal_id'))[:1] or journals[:1]
        status = filters.get('status') if filters.get('status') in ('todo', 'check', 'done', 'all') else 'todo'
        domain = Domain([('journal_id', '=', journal.id), ('move_id.state', '!=', 'cancel')])
        if status == 'todo':
            domain &= Domain([('is_reconciled', '=', False), ('move_id.review_state', 'not in', ('todo', 'anomaly'))])
        elif status == 'check':
            domain &= Domain('move_id.review_state', 'in', ('todo', 'anomaly'))
        elif status == 'done':
            domain &= Domain('is_reconciled', '=', True)
        if filters.get('date_from'):
            domain &= Domain('date', '>=', filters['date_from'])
        if filters.get('date_to'):
            domain &= Domain('date', '<=', filters['date_to'])
        search = (filters.get('search') or '').strip()
        if search:
            text = Domain.OR([Domain('payment_ref', 'ilike', search), Domain('partner_id', 'ilike', search),
                              Domain('partner_name', 'ilike', search)])
            try:
                amount = float(search.replace(',', ''))
            except ValueError:
                amount = None
            if amount is not None:
                text |= Domain('amount', 'in', (amount, -amount))
            domain &= text
        lines = self.search(domain, limit=self._KIT_REC_LIMIT + 1, order='date desc, id desc') if journal \
            else self.browse()
        cache = {}
        return {
            'journal': {'id': journal.id, 'name': journal.display_name,
                        'currency_id': (journal.currency_id or journal.company_id.currency_id).id},
            'journals': [{'id': j.id, 'name': j.display_name} for j in journals],
            'filters': {'journal_id': journal.id, 'status': status, 'search': search,
                        'date_from': filters.get('date_from') or '', 'date_to': filters.get('date_to') or ''},
            'rows': [line._kit_rec_row(cache) for line in lines[:self._KIT_REC_LIMIT]],
            'more': len(lines) > self._KIT_REC_LIMIT,
        }

    def _kit_rec_item(self, line, currency):
        """An open item as the drawer shows it."""
        discounted = self._discounted_residual(line, currency)
        return {
            'id': line.id,
            'name': line.move_id.name,
            'ref': line.move_id.ref or line.name or '',
            'date': fields.Date.to_string(line.date_maturity or line.date),
            'partner': line.partner_id.display_name or '',
            'residual': self._open_residual(line, currency),
            'discounted': discounted,
        }

    def kit_rec_line(self, partner_id=None):
        """Data of the drawer: suggestions (single items and items that add
        up), the manual models and what to tick by default.

        :param partner_id: suggest for this partner instead of the line's
        """
        self.ensure_one()
        cache = {}
        currency, transaction, _company = self._transaction_amounts()
        partner = self.env['res.partner'].browse(partner_id).exists().commercial_partner_id if partner_id \
            else self.partner_id.commercial_partner_id or self._detect_partner()
        suggestions = self._suggestions(cache, partner) if not self.is_reconciled else []
        singles = [dict(self._kit_rec_item(s['lines'], currency), score=s['score'], reasons=s['reasons'],
                        sure=s['sure'])
                   for s in suggestions if len(s['lines']) == 1]
        combinations = [{'items': [self._kit_rec_item(line, currency) for line in s['lines']],
                         'label': ' + '.join(s['lines'].move_id.mapped('name')),
                         'score': s['score'], 'reasons': s['reasons'], 'sure': s['sure']}
                        for s in suggestions if len(s['lines']) > 1]
        selected, gap = {}, 'open'
        best = next((s for s in suggestions if s['sure']), None) or \
            next((s for s in suggestions if s['score'] >= 55), None)
        if best:
            selected = {line.id: abs(self._open_residual(line, currency)) for line in best['lines']}
            if best.get('discount'):
                gap = 'discount'
        matched = self.matched_reconcile_model_id
        models = self._reconcile_models('manual')
        return {
            'row': self._kit_rec_row(cache),
            'amount': transaction,
            'currency_id': currency.id,
            'partner': {'id': partner.id, 'name': partner.display_name or ''},
            'suggestions': singles,
            'combinations': combinations,
            'selected': selected,
            'gap': gap,
            'models': [{'id': m.id, 'name': m.name, 'matched': m == matched}
                       for m in models.sorted(lambda m: m != matched)],
        }

    def kit_rec_search(self, text='', offset=0):
        """Open items the transaction can be matched with (core's matching
        domain), searched by number, reference, label, partner or amount;
        40 at a time."""
        self.ensure_one()
        currency, _transaction, _company = self._transaction_amounts()
        domain = Domain(self._get_default_amls_matching_domain())
        text = (text or '').strip()
        if text:
            match = Domain.OR([Domain('move_id.name', 'ilike', text), Domain('move_id.ref', 'ilike', text),
                               Domain('name', 'ilike', text), Domain('partner_id', 'ilike', text)])
            try:
                amount = float(text.replace(',', ''))
            except ValueError:
                amount = None
            if amount is not None:
                match |= Domain('amount_residual', 'in', (amount, -amount)) \
                    | Domain('amount_residual_currency', 'in', (amount, -amount))
            domain &= match
        lines = self.env['account.move.line'].search(domain, offset=int(offset or 0), limit=41,
                                                     order='date_maturity, id')
        items = [self._kit_rec_item(line, currency) for line in lines[:40]]
        return {'items': [item for item in items if item['residual'] is not None], 'more': len(lines) > 40}

    def _kit_rec_lock(self):
        """Lock the bank entry so two users cannot reconcile it at once."""
        self.check_access('write')
        if not self.move_id.try_lock_for_update():
            raise UserError(_("This transaction is being reconciled by another user. Try again in a moment."))

    def _kit_rec_plan(self, selection):
        """What a drawer selection books.

        :param selection: dict with
            ``items``: [journal item id, amount]: amount without sign, at most
            the open amount (None: all of it);
            ``writeoffs``: [{account_id, tax_ids, analytic_distribution,
            label, amount}]: lines booked to accounts (amount without sign,
            empty: what is still to book);
            ``gap``: what to do with the rest: 'open' (the last item takes
            it), 'discount' (core early payment discount), 'model' (booked
            with ``model_id``), 'suspense' (stays to reconcile).
        :return: dict ``items``, ``parts``, ``model``, ``discount``
        """
        currency, transaction, _company = self._transaction_amounts()
        wanted = {int(aml_id): amount for aml_id, amount in selection.get('items') or []}
        allowed = self.env['account.move.line'].search(
            Domain(self._get_default_amls_matching_domain()) & Domain('id', 'in', list(wanted)))
        if len(allowed) != len(wanted):
            raise UserError(_("An item is no longer open. Refresh the screen and try again."))
        items = []
        for line in allowed.sorted(lambda l: list(wanted).index(l.id)):
            residual = self._open_residual(line, currency)
            if residual is None:
                raise UserError(_("%s is in another currency than the transaction.", line.move_id.name))
            amount = wanted[line.id]
            value = abs(residual) if amount is None else min(abs(float(amount)), abs(residual))
            items.append((line, value if residual > 0 else -value))
        # Counterpart amount still to book (positive = debit).
        remaining = currency.round(sum(amount for _line, amount in items) - transaction)
        parts = []
        for writeoff in selection.get('writeoffs') or []:
            account = self.env['account.account'].browse(writeoff.get('account_id') or []).exists()
            if not account or self.company_id not in account.company_ids or account.account_type == 'off_balance':
                raise UserError(_("Choose an account of the company for each line."))
            sign = -1 if (remaining or -transaction) < 0 else 1  # sign of what is still to book
            value = abs(float(writeoff.get('amount') or 0.0)) or abs(remaining)
            taxes = self.env['account.tax'].browse(writeoff.get('tax_ids') or []).exists() \
                .filtered(lambda tax: tax.company_id.root_id == self.company_id.root_id)
            parts.append({
                'account': account,
                'amount': currency.round(sign * value),
                'taxes': taxes,
                'analytic_distribution': writeoff.get('analytic_distribution') or False,
                'label': writeoff.get('label') or False,
            })
            remaining = currency.round(remaining - sign * value)
        mode = selection.get('gap') or 'suspense'
        model, discount = None, False
        if not currency.is_zero(remaining):
            if mode == 'model':
                model_id = selection.get('model_id')
                model = (self._reconcile_models('manual') | self._reconcile_models('auto_reconcile')) \
                    .filtered(lambda m: m.id == model_id)
                if not model:
                    raise UserError(_("Choose a reconciliation model for the difference."))
                parts += self._reconcile_model_parts(model, remaining=remaining)
            elif mode == 'discount' and items:
                discount = True
            elif mode == 'open' and items:
                line, amount = items[-1]
                items[-1] = (line, amount - remaining)
        if not items and not parts:
            raise UserError(_("Select an item, a model or an account."))
        return {'items': items, 'parts': parts, 'model': model, 'discount': discount}

    def kit_rec_preview(self, selection):
        """The bank entry a selection would post (nothing is saved)."""
        self.ensure_one()
        try:
            plan = self._kit_rec_plan(selection)
        except UserError:
            plan = {'items': [], 'parts': [], 'discount': False}
        liquidity, vals_list = self._counterpart_entry_vals(
            self._items_counterpart_vals(plan['items'], plan['parts'], plan['discount']))
        accounts = self.env['account.account'].browse({vals['account_id'] for vals in [liquidity, *vals_list]})
        names = {account.id: account.display_name for account in accounts}
        lines = []
        for vals in [liquidity, *vals_list]:
            balance = vals['balance'] if 'balance' in vals else vals.get('debit', 0.0) - vals.get('credit', 0.0)
            lines.append({'account': names.get(vals['account_id'], ''), 'label': vals.get('name') or '',
                          'debit': max(balance, 0.0), 'credit': max(-balance, 0.0)})
        return {'currency_id': self.company_id.currency_id.id, 'lines': lines}

    def kit_rec_validate(self, selection):
        """Reconcile the transaction with what the user chose (see
        ``_kit_rec_plan``); ``partner_id`` and ``to_check`` are applied too.

        :return: the new row
        """
        self.ensure_one()
        if self.is_reconciled:
            raise UserError(_("This transaction is already reconciled."))
        self._kit_rec_lock()
        partner = self.env['res.partner'].browse(selection.get('partner_id') or []).exists()
        if partner and partner != self.partner_id:
            self.partner_id = partner
        plan = self._kit_rec_plan(selection)
        self._reconcile_items(plan['items'], plan['parts'], rule=plan['model'], discount=plan['discount'])
        if selection.get('to_check'):
            self.move_id.review_state = 'todo'
        return self._kit_rec_row({})

    def kit_rec_set_check(self, to_check):
        """Mark the bank entry to check (core review state) or reviewed."""
        self.check_access('write')
        self.move_id.review_state = 'todo' if to_check else 'reviewed'
        return True

    def kit_rec_undo(self):
        """Undo the reconciliation (core)."""
        self.check_access('write')
        self.action_undo_reconciliation()
        return True

    @api.model
    def kit_rec_accept_sure(self, line_ids):
        """Reconcile the sure matches among ``line_ids``; returns how many
        were reconciled."""
        lines = self.browse(line_ids).exists().filtered(lambda l: not l.is_reconciled)
        lines.check_access('write')
        return len(lines._auto_reconcile())

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

