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
"""Wizard generating the product performance report.

Security design
---------------
* The business searches (products, sale order lines) are never run as
  superuser, so record rules (own documents only, multi-company, ...) apply
  to the user who opens the report.
* Results are stored in ``product.performance.line`` transient records that
  belong to one wizard run (and one user). Nothing is written to the shared
  ``product.template`` records, so concurrent reports cannot overwrite each
  other.
* The only ``sudo()`` calls are the stock reads (moves and quants), which
  sales users may not be allowed to read. They are restricted to sale lines
  and products already found with the caller's rights and to the selected
  companies.
"""
from collections import defaultdict

from odoo import fields, models
from odoo.exceptions import UserError


class ProductPerformance(models.TransientModel):
    """Wizard model for generating product performance reports."""

    _name = 'product.performance'
    _inherit = 'performance.report.mixin'
    _description = "Product Performance Reports"

    def _get_default_category_id(self):
        """Get default category; returns first root category or False."""
        root_category = self.env['product.category'].search(
            [('parent_id', '=', False)], limit=1,
        )
        return root_category.id

    product_ids = fields.Many2many(
        comodel_name='product.template',
        help='Select products to filter the report',
        domain="[('categ_id', 'child_of', categ_id)]",
    )
    categ_id = fields.Many2one(
        comodel_name='product.category',
        string='Product Category',
        help='Select product category to filter products',
        default=lambda self: self._get_default_category_id(),
        required=True,
    )
    line_ids = fields.One2many(
        comodel_name='product.performance.line',
        inverse_name='wizard_id',
        string='Report Lines',
    )

    # ------------------------------------------------------------------
    # Scope helpers
    # ------------------------------------------------------------------
    def _get_products(self):
        """Return the product templates in scope (record rules apply)."""
        self.ensure_one()
        template = self.env['product.template']
        if self.product_ids:
            return template.search([('id', 'in', self.product_ids.ids)])
        return template.search([('categ_id', 'child_of', self.categ_id.id)])

    def _get_sale_line_domain(self, products, companies):
        """Domain on the confirmed sale lines used by every figure."""
        self.ensure_one()
        domain = [
            ('product_template_id', 'in', products.ids),
            ('company_id', 'in', companies.ids),
            ('state', '=', 'sale'),
        ]
        return domain + self._get_date_domain('order_id.date_order')

    # ------------------------------------------------------------------
    # Computation
    # ------------------------------------------------------------------
    def _get_returned_quantities(self, sale_line_domain, companies):
        """Return ``{(template_id, company_id): returned_qty}``.

        Stock moves are read with ``sudo()`` because sales users do not
        necessarily have stock rights. The sale lines are still selected with
        the caller's rights, so only visible sales can contribute.
        """
        line_ids = self.env['sale.order.line'].search(sale_line_domain).ids
        if not line_ids:
            return {}
        moves = self.env['stock.move'].sudo()._read_group(
            [
                ('sale_line_id', 'in', line_ids),
                ('picking_type_id.code', '=', 'incoming'),
                ('state', '=', 'done'),
                ('company_id', 'in', companies.ids),
            ],
            ['product_id', 'company_id'],
            ['quantity:sum'],
        )
        result = defaultdict(float)
        for product, company, quantity in moves:
            result[product.product_tmpl_id.id, company.id] += quantity
        return result

    def _get_main_warehouses(self, template_ids, companies):
        """Return the warehouse holding most stock of each template.

        :return: tuple of dicts ``({(tmpl, company): wh}, {tmpl: wh})``
        """
        quants = self.env['stock.quant'].sudo()._read_group(
            [
                ('product_id.product_tmpl_id', 'in', template_ids),
                ('location_id.usage', '=', 'internal'),
                ('company_id', 'in', companies.ids),
            ],
            ['product_id', 'company_id', 'location_id'],
            ['quantity:sum'],
        )
        best = {}
        best_any = {}
        for product, company, location, quantity in quants:
            warehouse = location.warehouse_id
            if not warehouse:
                continue
            tmpl_id = product.product_tmpl_id.id
            for store, key in ((best, (tmpl_id, company.id)),
                               (best_any, tmpl_id)):
                if key not in store or quantity > store[key][0]:
                    store[key] = (quantity, warehouse.id)
        return (
            {key: value[1] for key, value in best.items()},
            {key: value[1] for key, value in best_any.items()},
        )

    def _read_sales_figures(self, domain):
        """Aggregate the sale lines in the database.

        Amounts are converted to the currency of the company of the lines,
        so companies working in different currencies are never summed
        together.

        :return: ``{(template_id, company_id): defaultdict(float)}``
        """
        today = fields.Date.context_today(self)
        grouped = self.env['sale.order.line']._read_group(
            domain,
            ['product_id', 'company_id', 'currency_id'],
            ['price_subtotal:sum', 'product_uom_qty:sum',
              'qty_delivered:sum', 'price_unit:sum', '__count',
              'order_id:count_distinct'],
        )
        data = {}
        for (product, company, currency, revenue, ordered, delivered,
             price_sum, line_count, order_count) in grouped:
            target = company.currency_id
            values = data.setdefault(
                (product.product_tmpl_id.id, company.id), defaultdict(float))
            values['revenue'] += currency._convert(
                revenue, target, company, today)
            values['ordered'] += ordered
            values['delivered'] += delivered
            values['price_sum'] += currency._convert(
                price_sum, target, company, today)
            values['line_count'] += line_count
            values['order_count'] += order_count
        return data

    def _prepare_line_vals(self, products, companies):
        """Build the values of the report lines.

        ``Total Orders`` counts distinct orders per product variant; an order
        holding two variants of the same template is counted once for each.
        """
        self.ensure_one()
        env = self.env
        domain = self._get_sale_line_domain(products, companies)
        data = self._read_sales_figures(domain)

        # Products without any sale still appear in the report.
        sold = {key[0] for key in data}
        for template in products:
            if template.id not in sold:
                data[template.id, template.company_id.id] = defaultdict(
                    float)

        returned = self._get_returned_quantities(domain, companies)

        by_company = defaultdict(list)
        for tmpl_id, company_id in data:
            by_company[company_id].append(tmpl_id)
        on_hand = {}
        for company_id, tmpl_ids in by_company.items():
            scoped = env['product.template'].browse(tmpl_ids).with_context(
                allowed_company_ids=(
                    [company_id] if company_id else companies.ids))
            for template in scoped:
                on_hand[template.id, company_id] = template.qty_available
        warehouse, warehouse_any = self._get_main_warehouses(
            list({key[0] for key in data}), companies)

        vals_list = []
        for key, values in sorted(data.items(), key=lambda item: item[0]):
            tmpl_id, company_id = key
            company = (
                env['res.company'].browse(company_id)
                if company_id else env.company)
            orders = values['order_count']
            lines = values['line_count']
            vals_list.append({
                'wizard_id': self.id,
                'product_tmpl_id': tmpl_id,
                'company_id': company_id,
                'currency_id': company.currency_id.id,
                'warehouse_id': warehouse.get(key) or warehouse_any.get(
                    tmpl_id, False),
                'quantity': on_hand.get(key, 0.0),
                'revenue': values['revenue'],
                'total_order': int(orders),
                'ordered_quantities': values['ordered'],
                'delivered_quantities': values['delivered'],
                'returned_quantities': returned.get(key, 0.0),
                'avg_price': values['price_sum'] / lines if lines else 0.0,
                'avg_ordered_qty': (
                    values['ordered'] / orders if orders else 0.0),
                'avg_delivered_qty': (
                    values['delivered'] / orders if orders else 0.0),
            })
        return vals_list

    def action_product_performance(self):
        """Generate the report lines and open them.

        :return: action opening the product performance line list view
        :raises UserError: when no product matches the selection
        """
        self.ensure_one()
        companies = self._get_scope_companies()
        # Record rules (multi-company included) now apply to the selection.
        wizard = self.with_context(allowed_company_ids=companies.ids)
        products = wizard._get_products()
        if not products:
            raise UserError(self.env._("No products in this Company!"))
        wizard.line_ids.unlink()
        vals_list = wizard._prepare_line_vals(products, companies)
        wizard.env['product.performance.line'].create(vals_list)
        return {
            'name': self.env._('Product Performance Report'),
            'res_model': 'product.performance.line',
            'views': [(self.env.ref(
                'sales_product_performance_report.'
                'view_product_performance_line_list').id, 'list')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('wizard_id', '=', self.id)],
            'context': {'create': False, 'delete': False},
        }

    def product_performance(self):
        """Backward compatible wrapper for action_product_performance."""
        return self.action_product_performance()
