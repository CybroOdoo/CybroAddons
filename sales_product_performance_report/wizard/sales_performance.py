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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Wizard generating the sales performance report.

All searches run with the rights of the user who opens the report, so own
documents and multi-company record rules are honoured. Results are stored in
per-run transient lines: concurrent runs cannot overwrite each other and
nothing is written to shared users.
"""
from collections import defaultdict

from odoo import fields, models
from odoo.exceptions import UserError


class SalesPerformance(models.TransientModel):
    """Wizard model for generating sales performance reports."""

    _name = 'sales.performance'
    _inherit = 'performance.report.mixin'
    _description = "Sales Performance Reports"

    sales_team_ids = fields.Many2many(
        comodel_name='crm.team',
        domain="['|', ('company_id', '=', False), "
               "('company_id', 'in', company_ids)]",
        help='Select sales teams to filter the report',
    )
    sales_person_ids = fields.Many2many(
        comodel_name='res.users',
        domain="[('share', '=', False)]",
        help='Select sales persons to filter the report',
    )
    line_ids = fields.One2many(
        comodel_name='sales.performance.line',
        inverse_name='wizard_id',
        string='Report Lines',
    )

    # ------------------------------------------------------------------
    # Scope helpers
    # ------------------------------------------------------------------
    def _get_sales_persons(self, companies):
        """Return the sales persons in scope (record rules apply)."""
        self.ensure_one()
        users = self.env['res.users']
        if self.sales_person_ids:
            return users.search([('id', 'in', self.sales_person_ids.ids)])
        domain = [('share', '=', False), ('company_ids', 'in', companies.ids)]
        if self.sales_team_ids:
            domain.append(('crm_team_ids', 'in', self.sales_team_ids.ids))
        return users.search(domain)

    def _get_period_domain(self, companies):
        """Orders of the period, cancelled ones excluded."""
        self.ensure_one()
        domain = [
            ('company_id', 'in', companies.ids),
            ('state', '!=', 'cancel'),
        ]
        return domain + self._get_date_domain('date_order')

    def _get_order_domain(self, companies, user):
        """Orders of one sales person, as counted by the report."""
        return self._get_period_domain(companies) + [
            ('user_id', '=', user.id)]

    # ------------------------------------------------------------------
    # Computation
    # ------------------------------------------------------------------
    def _get_returned_order_ids(self, order_ids, companies):
        """Return the ids of the orders having at least one return.

        Pickings are read with ``sudo()`` because sales users do not
        necessarily have stock rights; ``order_ids`` were already selected
        with the caller's rights.
        """
        if not order_ids:
            return set()
        pickings = self.env['stock.picking'].sudo()._read_group(
            [
                ('sale_id', 'in', order_ids),
                ('picking_type_id.code', '=', 'incoming'),
                ('company_id', 'in', companies.ids),
            ],
            ['sale_id'],
            ['__count'],
        )
        return {order.id for order, _count in pickings}

    @staticmethod
    def _empty_figures():
        """Return the figures of a sales person without any order."""
        return {
            'orders': 0, 'done': 0, 'separate': 0,
            'estimated': 0.0, 'net': 0.0, 'ids': [],
        }

    def _read_order_figures(self, users, companies):
        """Aggregate the orders of ``users`` in the database.

        Amounts are converted to the currency of the company of the sales
        person. An order handled for a sales team other than the main team
        of the sales person is counted as ``separate``.

        :return: ``{user_id: dict}`` with the figures of each user
        """
        today = fields.Date.context_today(self)
        domain = self._get_period_domain(companies) + [
            ('user_id', 'in', users.ids)]
        grouped = self.env['sale.order']._read_group(
            domain,
            ['user_id', 'team_id', 'state', 'currency_id'],
            ['amount_total:sum', '__count', 'id:array_agg'],
        )
        figures = defaultdict(self._empty_figures)
        for user, team, state, currency, amount, count, ids in grouped:
            company = user.company_id
            amount = currency._convert(
                amount, company.currency_id, company, today)
            values = figures[user.id]
            values['orders'] += count
            values['estimated'] += amount
            if state == 'sale':
                values['done'] += count
                values['net'] += amount
            if team != user.sale_team_id:
                values['separate'] += count
            values['ids'].extend(ids)
        return figures

    def _prepare_line_vals(self, users, companies):
        """Build the values of the report lines."""
        self.ensure_one()
        figures = self._read_order_figures(users, companies)
        overall = self.env['sale.order'].search_count(
            self._get_period_domain(companies))
        all_ids = [oid for values in figures.values() for oid in values['ids']]
        returned = self._get_returned_order_ids(all_ids, companies)

        vals_list = []
        for user in users:
            values = figures[user.id]
            orders = values['orders']
            company = user.company_id
            vals_list.append({
                'wizard_id': self.id,
                'user_id': user.id,
                'team_id': user.sale_team_id.id,
                'company_id': company.id,
                'currency_id': company.currency_id.id,
                'total_sale_order': orders,
                'sale_order_done': values['done'],
                'estimated_revenue': values['estimated'],
                'net_revenue': values['net'],
                'avg_price': values['estimated'] / orders if orders else 0.0,
                'returned_orders': len(
                    returned.intersection(values['ids'])),
                'overall_performance': (
                    orders / overall * 100 if overall else 0.0),
                'overall_performance_separate': (
                    values['separate'] / overall * 100 if overall else 0.0),
            })
        return vals_list

    def action_sales_performance(self):
        """Generate the report lines and open them.

        :return: action opening the salesperson performance line list view
        :raises UserError: when no sales person matches the selection
        """
        self.ensure_one()
        companies = self._get_scope_companies()
        # Record rules (multi-company included) now apply to the selection.
        wizard = self.with_context(allowed_company_ids=companies.ids)
        users = wizard._get_sales_persons(companies)
        if not users:
            raise UserError(self.env._(
                "No Sales Persons found in %s!",
                ', '.join(companies.mapped('name'))))
        wizard.line_ids.unlink()
        vals_list = wizard._prepare_line_vals(users, companies)
        wizard.env['sales.performance.line'].create(vals_list)
        return {
            'name': self.env._('Sales Performance Report'),
            'res_model': 'sales.performance.line',
            'views': [(self.env.ref(
                'sales_product_performance_report.'
                'view_sales_performance_line_list').id, 'list')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('wizard_id', '=', self.id)],
            'context': {'create': False, 'delete': False},
        }

    def sales_performance(self):
        """Backward compatible wrapper for action_sales_performance."""
        return self.action_sales_performance()
