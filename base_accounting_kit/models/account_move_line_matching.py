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
"""Open Items mode of the reconciliation screen (P2.1-d): match invoices,
bills, payments and credit notes of a partner without a bank line. The
booking is core's ``account.move.line.reconcile()``; a difference can be
written off in a miscellaneous entry."""
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.fields import Command, Domain

ACCOUNT_TYPES = {
    'receivable': [('account_id.account_type', '=', 'asset_receivable')],
    'payable': [('account_id.account_type', '=', 'liability_payable')],
    'other': [('account_id.account_type', 'not in', ('asset_receivable', 'liability_payable', 'asset_cash',
                                                     'liability_credit_card'))],
}


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    _KIT_OPEN_LIMIT = 200

    # ------------------------------------------------------------------
    # Open items and suggestions
    # ------------------------------------------------------------------
    @api.model
    def _kit_open_domain(self, account_type=None):
        """Open items of reconcilable accounts in the allowed companies, of
        an account type (receivable / payable / other) when given."""
        return Domain([
            ('company_id', 'in', self.env.companies.ids),
            ('parent_state', '=', 'posted'),
            ('reconciled', '=', False),
            ('account_id.reconcile', '=', True),
            ('amount_residual', '!=', 0.0),
            ('display_type', 'not in', ('line_section', 'line_subsection', 'line_note')),
            *ACCOUNT_TYPES.get(account_type, []),
        ])

    def _kit_open_mentions(self, other):
        """Whether the label or reference of ``self`` names the entry of
        ``other`` (its number or payment reference)."""
        text = ' '.join(filter(None, (self.name, self.ref, self.move_id.ref, self.move_id.name,
                                      self.move_id.payment_reference))).lower()
        move = other.move_id
        return any(ref and len(ref) >= 3 and ref.lower() in text
                   for ref in (move.name, move.payment_reference) if ref != self.move_id.name)

    def _kit_open_discounted(self, date):
        """Open amount after core's early payment discount when it is still
        allowed on ``date``, else None."""
        currency = self.currency_id
        if self.display_type == 'payment_term' and self.discount_amount_currency \
                and currency == self.company_currency_id \
                and self.move_id._is_eligible_for_early_payment_discount(currency, date):
            return self.discount_amount_currency
        return None

    def _kit_open_suggestions(self):
        """Ranked suggestions among the open items ``self`` (one partner,
        one account). Each: ``lines``, ``label``, ``reasons``, ``sure``,
        ``discount``.

        - everything nets to 0: sure;
        - a credit and a debit of the same amount where one names the
          other (or the early payment discount amount): sure;
        - the only debit with the amount of a credit: please confirm;
        - debits that add up to a credit: please confirm.
        """
        currency = self.company_currency_id[:1]
        if not currency or not self:
            return []
        debits = self.filtered(lambda l: l.amount_residual > 0).sorted(lambda l: (l.date_maturity or l.date, l.id))
        credits = self.filtered(lambda l: l.amount_residual < 0).sorted(lambda l: (l.date_maturity or l.date, l.id))
        if not debits or not credits:
            return []
        suggestions = []
        if currency.is_zero(sum(self.mapped('amount_residual'))):
            suggestions.append({'lines': self, 'reasons': [_("The items net to zero")], 'sure': True,
                                'discount': False})
        used = self.browse()
        for credit in credits:
            amount = -credit.amount_residual
            same = debits.filtered(lambda d: currency.compare_amounts(d.amount_residual, amount) == 0)
            named = same.filtered(lambda d: credit._kit_open_mentions(d) or d._kit_open_mentions(credit))
            early = debits.filtered(lambda d: (disc := d._kit_open_discounted(credit.date)) is not None
                                    and currency.compare_amounts(disc, amount) == 0)
            if named - used:
                debit = (named - used)[:1]
                suggestions.append({'lines': debit | credit, 'sure': True, 'discount': False,
                                    'reasons': [_("Same amount"), _("Reference in label")]})
            elif early - used:
                debit = (early - used)[:1]
                suggestions.append({'lines': debit | credit, 'sure': True, 'discount': True,
                                    'reasons': [_("Early payment discount")]})
            elif len(same - used) == 1:
                debit = same - used
                suggestions.append({'lines': debit | credit, 'sure': False, 'discount': False,
                                    'reasons': [_("Same amount")]})
            else:
                combination = self.env['account.bank.statement.line']._find_combination(
                    [(d, d.amount_residual) for d in debits - used], amount, currency)
                if combination:
                    suggestions.append({'lines': combination | credit, 'sure': False, 'discount': False,
                                        'reasons': [_("Add up to the amount")]})
                    debit = combination
                else:
                    continue
            used |= debit | credit
        for suggestion in suggestions:
            suggestion['label'] = ' + '.join(suggestion['lines'].move_id.mapped('name'))
        # Sure first, then the order found (oldest credits first).
        suggestions.sort(key=lambda s: not s['sure'])
        return suggestions

    @api.model
    def kit_open_load(self, filters=None):
        """Partners (per account) with open debits and credits to match,
        grouped like the bank side: sure / confirm / needs."""
        filters = dict(filters or {})
        account_type = filters.get('account_type') if filters.get('account_type') in ACCOUNT_TYPES else 'receivable'
        domain = self._kit_open_domain(account_type) & Domain('partner_id', '!=', False)
        if filters.get('partner_id'):
            domain &= Domain('partner_id', 'child_of', filters['partner_id'])
        search = (filters.get('search') or '').strip()
        if search:
            domain &= Domain.OR([Domain('partner_id', 'ilike', search), Domain('move_id.name', 'ilike', search),
                                 Domain('move_id.ref', 'ilike', search)])
        # Partners (per account) with both open debits and open credits;
        # contacts count for their company.
        sides = {}
        for sign, side in (('>', 'debit'), ('<', 'credit')):
            for partner, account in self._read_group(domain & Domain('amount_residual', sign, 0.0),
                                                     ['partner_id', 'account_id']):
                sides.setdefault((partner.commercial_partner_id, account), set()).add(side)
        keys = sorted((key for key, found in sides.items() if len(found) == 2),
                      key=lambda k: (k[0].display_name or '', k[1].code or ''))
        rows = []
        for partner, account in keys[:self._KIT_OPEN_LIMIT]:
            rows.append(self._kit_open_row(partner, account))
        company = self.env.company
        return {
            'filters': {'account_type': account_type, 'search': search, 'partner_id': filters.get('partner_id') or False},
            'currency_id': company.currency_id.id,
            'rows': rows,
            'more': len(keys) > self._KIT_OPEN_LIMIT,
        }

    @api.model
    def _kit_open_items(self, partner, account):
        """Open items of a partner (and its contacts) on an account, oldest first."""
        return self.search(self._kit_open_domain() & Domain([
            ('partner_id', 'child_of', partner.id), ('account_id', '=', account.id)]),
            order='date_maturity, date, id')

    @api.model
    def _kit_open_row(self, partner, account):
        items = self._kit_open_items(partner, account)
        debits = items.filtered(lambda l: l.amount_residual > 0)
        credits = items - debits
        suggestions = items._kit_open_suggestions()
        if any(s['sure'] for s in suggestions):
            group = 'sure'
        elif suggestions:
            group = 'confirm'
        else:
            group = 'needs'
        best = suggestions[:1]
        return {
            'id': '%s-%s' % (partner.id, account.id),
            'partner_id': partner.id,
            'account_id': account.id,
            'label': partner.display_name,
            'subtitle': ' · '.join((
                _("1 debit") if len(debits) == 1 else _("%s debits", len(debits)),
                _("1 credit") if len(credits) == 1 else _("%s credits", len(credits)),
                account.display_name)),
            'date': fields.Date.to_string(min(items.mapped('date'))) if items else False,
            'amount': sum(items.mapped('amount_residual')),
            'currency_id': items.company_currency_id[:1].id,
            'partner': '',
            'partner_found': '',
            'group': group,
            'proposal': best[0]['label'] if best else '',
            'reasons': best[0]['reasons'] if best else [],
            'reconciled': False,
            'to_check': False,
        }

    def _kit_open_item(self):
        self.ensure_one()
        return {
            'id': self.id,
            'name': self.move_id.name,
            'ref': self.move_id.ref or (self.name if self.name != self.move_id.name else '') or '',
            'date': fields.Date.to_string(self.date_maturity or self.date),
            'partner': self.partner_id.display_name or '',
            'residual': self.amount_residual,
            'discounted': self.discount_balance if self.display_type == 'payment_term' and self.discount_amount_currency
            and self.move_id.invoice_payment_term_id.early_discount else None,
        }

    @api.model
    def _kit_open_writeoff_journals(self):
        return self.env['account.journal'].search([
            *self.env['account.journal']._check_company_domain(self.env.company), ('type', '=', 'general')])

    @api.model
    def kit_open_partner(self, partner_id, account_id):
        """Drawer data for a partner and an account: debits, credits, the
        suggestions and what to tick by default."""
        partner = self.env['res.partner'].browse(partner_id).exists()
        account = self.env['account.account'].browse(account_id).exists()
        items = self._kit_open_items(partner, account)
        suggestions = items._kit_open_suggestions()
        best = suggestions[:1]
        journals = self._kit_open_writeoff_journals()
        models = self.env['account.reconcile.model'].search([
            ('company_id', 'in', (self.env.company.id, False)), ('rule_type', '!=', 'matching_rule'),
        ]).filtered(lambda m: m.line_ids.filtered('account_id'))
        return {
            'row': self._kit_open_row(partner, account),
            'mode': 'open',
            'partner': {'id': partner.id, 'name': partner.display_name},
            'account': {'id': account.id, 'name': account.display_name},
            'currency_id': self.env.company.currency_id.id,
            'debits': [line._kit_open_item() for line in items.filtered(lambda l: l.amount_residual > 0)],
            'credits': [line._kit_open_item() for line in items.filtered(lambda l: l.amount_residual < 0)],
            'suggestions': [{'ids': s['lines'].ids, 'label': s['label'], 'reasons': s['reasons'],
                             'sure': s['sure'], 'discount': s['discount']} for s in suggestions],
            'selected': best[0]['lines'].ids if best else [],
            'gap': 'discount' if best and best[0]['discount'] else 'open',
            'journals': [{'id': j.id, 'name': j.display_name} for j in journals],
            'journal_id': journals[:1].id,
            'date': fields.Date.to_string(fields.Date.context_today(self)),
            'models': [{'id': m.id, 'name': m.name, 'matched': False} for m in models],
        }

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    @api.model
    def _kit_open_plan(self, selection):
        """Selected items and the write-off entry values for the
        difference (if any).

        :param selection: dict ``account_id``, ``partner_id``, ``items``
            (ids), ``gap`` ('open': keep the rest open, 'writeoff': book it
            on ``writeoffs`` lines, 'model': with ``model_id``, 'discount':
            core early payment discount), ``journal_id``, ``date``
        :return: (journal items, write-off move values or None)
        """
        account = self.env['account.account'].browse(selection.get('account_id') or []).exists()
        partner = self.env['res.partner'].browse(selection.get('partner_id') or []).exists()
        ids = [int(i) for i in selection.get('items') or []]
        lines = self.search(self._kit_open_domain() & Domain([
            ('id', 'in', ids), ('account_id', '=', account.id), ('partner_id', 'child_of', partner.id)]))
        if len(lines) != len(ids):
            raise UserError(_("An item is no longer open. Refresh the screen and try again."))
        if not lines:
            raise UserError(_("Select the items to match."))
        lines.check_access('write')
        company = lines.company_id[:1]
        currency = company.currency_id
        difference = currency.round(sum(lines.mapped('amount_residual')))
        mode = selection.get('gap') or 'open'
        if currency.is_zero(difference) or mode == 'open':
            if len(lines) < 2:
                raise UserError(_("Select at least one debit and one credit, or write off the difference."))
            return lines, None
        journal = self.env['account.journal'].browse(selection.get('journal_id') or []).exists() \
            .filtered(lambda j: j.company_id == company and j.type == 'general')
        if not journal:
            raise UserError(_("Choose a miscellaneous journal for the write-off."))
        date = fields.Date.to_date(selection.get('date')) or fields.Date.context_today(self)
        label = _("Write-off %s", partner.display_name)
        counterpart = {'account_id': account.id, 'partner_id': partner.id, 'name': label,
                       'balance': -difference, 'currency_id': currency.id, 'amount_currency': -difference}
        if mode == 'discount':
            values = [{'aml': line, 'amount_currency': -line.amount_residual_currency, 'balance': -line.amount_residual}
                      for line in lines.filtered(lambda l: l._kit_open_discounted(date) is not None)]
            if not values:
                raise UserError(_("No early payment discount applies on this date."))
            res = self.env['account.move']._get_invoice_counterpart_amls_for_early_payment_discount(values, difference)
            others = [dict(vals) for group in res.values() for vals in group]
        else:
            parts = []
            if mode == 'model':
                model = self.env['account.reconcile.model'].browse(selection.get('model_id') or []).exists() \
                    .filtered(lambda m: m.company_id == company)
                if not model:
                    raise UserError(_("Choose a reconciliation model for the difference."))
                remaining = difference
                for model_line in model.line_ids.filtered('account_id'):
                    if model_line.amount_type in ('percentage', 'percentage_st_line'):
                        amount = currency.round(remaining * model_line.amount / 100.0)
                    elif model_line.amount_type == 'fixed':
                        amount = currency.round(model_line.amount if difference > 0 else -model_line.amount)
                    else:
                        continue
                    parts.append({'account': model_line.account_id, 'amount': amount, 'taxes': model_line.tax_ids,
                                  'analytic_distribution': model_line.analytic_distribution,
                                  'label': model_line.label, 'model': model})
                    remaining -= amount
            else:
                remaining = difference
                for writeoff in selection.get('writeoffs') or []:
                    target = self.env['account.account'].browse(writeoff.get('account_id') or []).exists()
                    if not target or company not in target.company_ids or target.account_type == 'off_balance':
                        raise UserError(_("Choose an account of the company for each line."))
                    value = abs(float(writeoff.get('amount') or 0.0)) or abs(remaining)
                    amount = currency.round(value if difference > 0 else -value)
                    parts.append({'account': target, 'amount': amount,
                                  'taxes': self.env['account.tax'].browse(writeoff.get('tax_ids') or []).exists(),
                                  'analytic_distribution': writeoff.get('analytic_distribution') or False,
                                  'label': writeoff.get('label') or False})
                    remaining -= amount
            if not parts:
                raise UserError(_("Add a write-off line or choose a model."))
            if not currency.is_zero(currency.round(remaining)):
                raise UserError(_("The write-off lines must add up to the difference."))
            others = []
            for part in parts:
                taxes = part['taxes']
                base = part['amount']
                if taxes:
                    res = taxes.with_context(force_price_include=True).compute_all(abs(base), currency=currency)
                    base = res['total_excluded'] if base > 0 else -res['total_excluded']
                others.append({
                    'account_id': part['account'].id, 'partner_id': partner.id, 'name': part['label'] or label,
                    'balance': base, 'currency_id': currency.id, 'amount_currency': base,
                    'tax_ids': [Command.set(taxes.ids)], 'analytic_distribution': part['analytic_distribution'],
                    'reconcile_model_id': part['model'].id if part.get('model') else False,
                })
        move_vals = {
            'move_type': 'entry', 'journal_id': journal.id, 'date': date, 'ref': label,
            'line_ids': [Command.create(counterpart)] + [Command.create(vals) for vals in others],
        }
        return lines, move_vals

    @api.model
    def kit_open_preview(self, selection):
        """What Validate would do: the items and the write-off entry lines
        (nothing is saved)."""
        try:
            lines, move_vals = self._kit_open_plan(selection)
        except UserError as error:
            return {'error': str(error), 'lines': []}
        entry = self._kit_open_entry_preview(move_vals) if move_vals else []
        return {'error': False, 'currency_id': self.env.company.currency_id.id, 'lines': entry,
                'items': len(lines)}

    @api.model
    def _kit_open_entry_preview(self, move_vals):
        """Lines of the write-off entry as it will be posted: the given
        lines plus the tax lines core adds for their taxes."""
        currency = self.env.company.currency_id
        rows = []
        for command in move_vals['line_ids']:
            vals = command[2]
            rows.append((vals['account_id'], vals.get('name') or '', vals['balance']))
            tax_ids = vals.get('tax_ids') and vals['tax_ids'][0][2]
            if tax_ids:
                base = vals['balance']
                res = self.env['account.tax'].browse(tax_ids).compute_all(abs(base), currency=currency)
                for tax in res['taxes']:
                    amount = tax['amount'] if base > 0 else -tax['amount']
                    rows.append((tax['account_id'] or vals['account_id'], tax['name'], amount))
        accounts = {a.id: a.display_name for a in self.env['account.account'].browse({r[0] for r in rows})}
        return [{'account': accounts.get(account, ''), 'label': label,
                 'debit': max(balance, 0.0), 'credit': max(-balance, 0.0)} for account, label, balance in rows]

    @api.model
    def kit_open_validate(self, selection):
        """Post the write-off entry (if any) and reconcile with core."""
        lines, move_vals = self._kit_open_plan(selection)
        if move_vals:
            move = self.env['account.move'].create(move_vals)
            move.action_post()
            lines |= move.line_ids.filtered(lambda l: l.account_id == lines.account_id[:1] and not l.reconciled)
        lines.reconcile()
        return True

    @api.model
    def kit_open_accept_sure(self, keys):
        """Reconcile the sure suggestions of the given partner/account rows;
        returns how many matches were made."""
        count = 0
        for key in keys or []:
            partner_id, account_id = (int(part) for part in str(key).split('-'))
            partner = self.env['res.partner'].browse(partner_id).exists()
            account = self.env['account.account'].browse(account_id).exists()
            items = self._kit_open_items(partner, account)
            items.check_access('write')
            for suggestion in [s for s in items._kit_open_suggestions() if s['sure']]:
                lines = suggestion['lines'].filtered(lambda l: not l.reconciled)
                if len(lines) < 2:
                    continue
                with self.env.cr.savepoint():
                    self.kit_open_validate({
                        'account_id': account.id, 'partner_id': partner.id, 'items': lines.ids,
                        'gap': 'discount' if suggestion['discount'] else 'open',
                        'journal_id': self._kit_open_writeoff_journals()[:1].id,
                        'date': fields.Date.to_string(max(lines.mapped('date'))),
                    })
                    count += 1
        return count

    # ------------------------------------------------------------------
    # Journal items list: Reconcile
    # ------------------------------------------------------------------
    def action_kit_reconcile(self):
        """Reconcile the selected journal items when they net to zero on
        one account; otherwise open the Open Items screen on them."""
        lines = self.filtered(lambda l: not l.reconciled and l.parent_state == 'posted')
        if not lines:
            raise UserError(_("Select open, posted journal items."))
        if len(lines.account_id) > 1 or not lines.account_id.reconcile:
            raise UserError(_("Select items of one account that allows reconciliation."))
        lines.check_access('write')
        if lines.company_currency_id.is_zero(sum(lines.mapped('amount_residual'))) and len(lines) > 1:
            lines.reconcile()
            return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {
                'type': 'success', 'message': _("%s items reconciled.", len(lines)),
                'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'}}}
        partner = lines.partner_id.commercial_partner_id
        if len(partner) != 1:
            raise UserError(_("The items do not net to zero: select the items of one partner to match them."))
        action = self.env['ir.actions.actions']._for_xml_id('base_accounting_kit.action_kit_open_items')
        action['params'] = {'mode': 'open', 'partner_id': partner.id, 'account_id': lines.account_id.id,
                            'selected': lines.ids}
        return action
