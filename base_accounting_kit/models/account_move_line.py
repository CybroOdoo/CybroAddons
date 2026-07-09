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
import ast
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from dateutil.relativedelta import relativedelta


class AccountInvoiceLine(models.Model):
    """Define a model for account invoice lines with fields related to assets and their management."""
    _inherit = 'account.move.line'

    asset_category_id = fields.Many2one('account.asset.category',
                                        string='Asset Category')
    asset_start_date = fields.Date(string='Asset Start Date',
                                   compute='_get_asset_date', readonly=True,
                                   store=True)
    asset_end_date = fields.Date(string='Asset End Date',
                                 compute='_get_asset_date', readonly=True,
                                 store=True)
    asset_mrr = fields.Float(string='Monthly Recurring Revenue',
                             compute='_get_asset_date',
                             readonly=True, digits='Account',
                             store=True)

    @api.depends('asset_category_id', 'move_id.invoice_date')
    def _get_asset_date(self):
        """Returns the asset_start_date and the asset_end_date of the Asset"""
        for record in self:
            record.asset_mrr = 0
            record.asset_start_date = False
            record.asset_end_date = False
            cat = record.asset_category_id
            if cat:
                if cat.method_number == 0 or cat.method_period == 0:
                    raise UserError(_(
                        'The number of depreciations or the period length of '
                        'your asset category cannot be null.'))
                months = cat.method_number * cat.method_period
                if record.move_id.move_type in ('out_invoice', 'out_refund'):
                    record.asset_mrr = record.price_subtotal_signed / months
                if record.move_id.invoice_date:
                    start_date = datetime.strptime(
                        str(record.move_id.invoice_date), DF).replace(day=1)
                    end_date = (start_date + relativedelta(months=months,
                                                           days=-1))
                    record.asset_start_date = start_date.strftime(DF)
                    record.asset_end_date = end_date.strftime(DF)

    def _get_asset_category(self):
        """Return the asset/deferred-revenue category for this line: the one
        set on the line, else the product's category based on the move type."""
        self.ensure_one()
        if self.asset_category_id:
            return self.asset_category_id
        tmpl = self.product_id.product_tmpl_id
        if self.move_id.move_type in ('in_invoice', 'in_refund'):
            return tmpl.asset_category_id
        if self.move_id.move_type in ('out_invoice', 'out_refund'):
            return tmpl.deferred_revenue_category_id
        return self.env['account.asset.category']

    def asset_create(self):
        """Create the asset/deferred-revenue record for lines that resolve to
        an asset category (from the line or, as a fallback, the product)."""
        for record in self:
            category = record._get_asset_category()
            if category:
                vals = {
                    'name': record.name,
                    'code': record.move_id.name or False,
                    'category_id': category.id,
                    'value': record.price_subtotal,
                    'partner_id': record.partner_id.id,
                    'company_id': record.move_id.company_id.id,
                    'currency_id': record.move_id.company_currency_id.id,
                    'date': record.move_id.invoice_date,
                    'invoice_id': record.move_id.id,
                }
                changed_vals = record.env[
                    'account.asset.asset'].onchange_category_id_values(
                    category.id)
                vals.update(changed_vals['value'])
                asset = record.env['account.asset.asset'].create(vals)
                if category.open_asset:
                    asset.validate()
        return True

    @api.onchange('asset_category_id')
    def onchange_asset_category_id(self):
        """Set the account from the selected asset category."""
        if self.asset_category_id and self.move_id.move_type in (
                'out_invoice', 'in_invoice'):
            self.account_id = self.asset_category_id.account_asset_id

    @api.onchange('product_id')
    def _onchange_product_id_asset(self):
        """Populate the asset/deferred-revenue category from the product."""
        if self.product_id:
            tmpl = self.product_id.product_tmpl_id
            if self.move_id.move_type == 'out_invoice':
                self.asset_category_id = tmpl.deferred_revenue_category_id
            elif self.move_id.move_type == 'in_invoice':
                self.asset_category_id = tmpl.asset_category_id

    @api.model
    def _query_get(self, domain=None):
        """Used to add domain constraints to the query"""
        self.check_access('read')

        context = dict(self.env.context or {})
        domain = domain or []
        if not isinstance(domain, (list, tuple)):
            domain = ast.literal_eval(domain)

        date_field = 'date'
        if context.get('aged_balance'):
            date_field = 'date_maturity'
        if context.get('date_to'):
            domain += [(date_field, '<=', context['date_to'])]
        if context.get('date_from'):
            if not context.get('strict_range'):
                domain += ['|', (date_field, '>=', context['date_from']),
                           ('account_id.include_initial_balance', '=', True)]
            elif context.get('initial_bal'):
                domain += [(date_field, '<', context['date_from'])]
            else:
                domain += [(date_field, '>=', context['date_from'])]

        if context.get('journal_ids'):
            domain += [('journal_id', 'in', context['journal_ids'])]

        state = context.get('state')
        if state and state.lower() != 'all':
            domain += [('parent_state', '=', state)]

        if context.get('company_id'):
            domain += [('company_id', '=', context['company_id'])]
        elif context.get('allowed_company_ids'):
            domain += [('company_id', 'in', self.env.companies.ids)]
        else:
            domain += [('company_id', '=', self.env.company.id)]

        if context.get('reconcile_date'):
            domain += ['|', ('reconciled', '=', False), '|',
                       ('matched_debit_ids.max_date', '>', context['reconcile_date']),
                       ('matched_credit_ids.max_date', '>', context['reconcile_date'])]

        if context.get('account_tag_ids'):
            domain += [('account_id.tag_ids', 'in', context['account_tag_ids'].ids)]

        if context.get('account_ids'):
            domain += [('account_id', 'in', context['account_ids'].ids)]

        if context.get('partner_ids'):
            domain += [('partner_id', 'in', context['partner_ids'].ids)]

        if context.get('partner_categories'):
            domain += [('partner_id.category_id', 'in', context['partner_categories'].ids)]

        where_clause = ""
        where_clause_params = []
        tables = ''
        if domain:
            domain.append(('display_type', 'not in', ('line_section', 'line_note')))
            domain.append(('parent_state', '!=', 'cancel'))
            query = self._search(domain, bypass_access=True)
            # In Odoo 19 ``Query.from_clause``/``where_clause`` return
            # ``odoo.tools.SQL`` objects (code + params) instead of the old
            # ``(str, params)`` tuples. Expose the composed SQL string and its
            # parameters so the legacy raw-SQL report parsers keep working.
            from_sql = query.from_clause
            where_sql = query.where_clause
            tables = from_sql.code
            where_clause = where_sql.code
            where_clause_params = list(from_sql.params) + list(where_sql.params)
        return tables, where_clause, where_clause_params
