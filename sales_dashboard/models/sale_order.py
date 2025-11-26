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
from odoo import models, api, fields
from datetime import date, timedelta
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """Extends sale.order model to fetch data to be displayed in the dashboard"""
    _inherit = 'sale.order'

    def _get_range(self, filter_key, custom_start=None, custom_end=None):
        """Manages the date range according to the filter selected"""
        today = date.today()

        if filter_key == 'this_week':
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            return start, min(end, today)

        elif filter_key == 'this_month':
            return today.replace(day=1), today

        elif filter_key == 'this_year':
            return today.replace(month=1, day=1), today

        elif filter_key == 'custom' and custom_start and custom_end:
            if custom_end < custom_start:
                raise UserError("Please select a valid range")
            return custom_start, custom_end

        return None, None

    def _build_global_domain(self, base_domain, filters, date_field="date_order"):
        """Build domain with global filter applied"""
        global_filter = filters.get("global_filter", "this_week")
        if global_filter == "select_period":
            global_filter = "this_week"

        if global_filter == "custom":
            custom_range = filters.get("custom_range", {})
            custom_start = custom_range.get("from")
            custom_end = custom_range.get("to")
        else:
            custom_start = None
            custom_end = None

        from_date, to_date = self._get_range(global_filter, custom_start, custom_end)

        domain = base_domain.copy()
        if from_date:
            domain.append((date_field, '>=', from_date))
        if to_date:
            domain.append((date_field, '<=', to_date))
        return domain

    @api.model
    def get_tile_domain(self, base_domain, filters):
        """Get domain for tile clicks with global filter applied"""
        filterss = self._build_global_domain(base_domain, filters)
        return self._build_global_domain(base_domain, filters)

    @api.model
    def get_sales_dashboard_data(self, filters=None):
        """Fetches the datas to be displayed"""
        filters = filters or {}
        limit = int(filters.get("limit", 10))

        def get_filter_key(specific_filter_key):
            """Build and return a domain combining base_domain with global date filters."""
            global_filter = filters.get("global_filter", "this_week")
            if global_filter == "custom":
                return "custom"
            elif global_filter == "select_period":
                return filters.get(specific_filter_key, "this_week")
            else:
                return global_filter

        def build_domain(base_domain, specific_filter_key, date_field="date_order"):
            """Attach date domain based on the filter key"""
            filter_key = get_filter_key(specific_filter_key)

            if filter_key == "custom":
                custom_range = filters.get("custom_range", {})
                custom_start = custom_range.get("from")
                custom_end = custom_range.get("to")
            else:
                custom_start = None
                custom_end = None

            from_date, to_date = self._get_range(filter_key, custom_start, custom_end)

            domain = base_domain.copy()
            if from_date:
                domain.append((date_field, '>=', from_date))
            if to_date:
                domain.append((date_field, '<=', to_date))
            return domain

        team_domain = build_domain([('state', 'in', ['sale', 'done'])], "team_filter")
        sales_by_team = self.read_group(team_domain, ['amount_total'], ['team_id'], limit=limit, orderby='amount_total desc')
        teams = [
            {'id': rec['team_id'][0], 'name': rec['team_id'][1], 'amount': rec['amount_total']}
            for rec in sales_by_team if rec['team_id']
        ]

        person_domain = build_domain([('state', 'in', ['sale', 'done'])], "person_filter")
        sales_by_person = self.read_group(person_domain, ['amount_total'], ['user_id'], limit=limit, orderby='amount_total desc')
        persons = [
            {'id': rec['user_id'][0], 'name': rec['user_id'][1], 'amount': rec['amount_total']}
            for rec in sales_by_person if rec['user_id']
        ]

        customer_domain = build_domain([('state', 'in', ['sale', 'done'])], "customer_filter")
        customers_grouped = self.read_group(customer_domain, ['amount_total'], ['partner_id'],
                                            limit=limit, orderby='amount_total desc')
        customers = [
            {'id': rec['partner_id'][0], 'name': rec['partner_id'][1], 'amount': rec['amount_total']}
            for rec in customers_grouped if rec['partner_id']
        ]

        product_domain = build_domain([('order_id.state', 'in', ['sale', 'done'])],
                                      "product_filter", "order_id.date_order")
        if filters.get("product_category_id"):
            product_domain.append(('product_id.categ_id', '=', filters["product_category_id"]))
        top_products_grouped = self.env['sale.order.line'].read_group(
            product_domain, ['product_uom_qty'], ['product_id'],
            limit=limit, orderby='product_uom_qty desc'
        )
        top_products = [
            {'id': rec['product_id'][0], 'name': rec['product_id'][1], 'qty': rec['product_uom_qty']}
            for rec in top_products_grouped if rec['product_id']
        ]

        low_product_domain = build_domain([('order_id.state', 'in', ['sale', 'done'])],
                                          "low_product_filter", "order_id.date_order")
        if filters.get("low_product_category_id"):
            low_product_domain.append(('product_id.categ_id', '=', filters["low_product_category_id"]))
        low_products_grouped = self.env['sale.order.line'].read_group(
            low_product_domain, ['product_uom_qty'], ['product_id'],
            limit=limit, orderby='product_uom_qty asc'
        )
        low_products = [
            {'id': rec['product_id'][0], 'name': rec['product_id'][1], 'qty': rec['product_uom_qty']}
            for rec in low_products_grouped if rec['product_id']
        ]

        order_domain = build_domain([], "order_filter")
        order_status_grouped = self.read_group(order_domain, ['id'], ['state'])
        ORDER_STATUS_LABELS = {
            'draft': 'Quotation',
            'sent': 'Quotation Sent',
            'sale': 'Sales Order',
            'done': 'Locked',
            'cancel': 'Cancelled',
        }
        order_status = [
            {'status': ORDER_STATUS_LABELS.get(rec['state'], rec['state'].capitalize()),
             'count': rec['state_count']}
            for rec in order_status_grouped
        ]

        invoice_domain = build_domain([('move_type', '=', 'out_invoice')], "invoice_filter", "invoice_date")
        invoice_status_grouped = self.env['account.move'].read_group(invoice_domain, ['id'], ['state'])
        INVOICE_STATUS_LABELS = {
            'draft': 'Draft',
            'posted': 'Posted',
            'cancel': 'Cancelled',
        }
        invoice_status = [
            {'status': INVOICE_STATUS_LABELS.get(rec['state'], rec['state'].capitalize()),
             'count': rec['state_count']}
            for rec in invoice_status_grouped
        ]

        overdue_customers_domain =build_domain([
            ('move_type', '=', 'out_invoice'),
            ('payment_state', '!=', 'paid'),
            ('invoice_date_due', '<', fields.Date.today())
        ],"overdue_filter","invoice_date")
        overdue_customers_grouped = self.env['account.move'].read_group(
            overdue_customers_domain, ['amount_total'], ['partner_id'], orderby='amount_total desc', limit=limit
        )
        overdue_customers =[
            {'id': rec['partner_id'][0], 'name': rec['partner_id'][1], 'amount': rec['amount_total']}
            for rec in overdue_customers_grouped if rec['partner_id']
        ]

        categories = self.env['product.category'].search([])
        product_categories = [{'id': c.id, 'name': c.display_name} for c in categories]

        sale_orders_domain = build_domain([('state', 'in', ['sale', 'done'])], "order_tile_filter")
        sale_orders = self.search_count(sale_orders_domain)

        quotations_domain = build_domain([('state', 'in', ['draft', 'sent'])], "quotation_tile_filter")
        quotations = self.search_count(quotations_domain)

        orders_to_invoice_domain = build_domain([('invoice_status', '=', 'to invoice')], "to_invoice_tile_filter")
        orders_to_invoice = self.search_count(orders_to_invoice_domain)

        orders_fully_invoiced_domain = build_domain([('invoice_status', '=', 'invoiced')], "invoiced_tile_filter")
        orders_fully_invoiced = self.search_count(orders_fully_invoiced_domain)

        conversion_rate = round(
            (sale_orders / (quotations + sale_orders) * 100) if (quotations + sale_orders) > 0 else 0)

        SaleOrder = self.env['sale.order']
        company_currency = self.env.company.currency_id
        today = fields.Date.today()
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)

        def _get_total(start_date):
            """To find the total amount by grouping the orders based on the currency"""
            groups = SaleOrder.read_group(
                [('state', '=', 'sale'), ('date_order', '>=', start_date)],
                ['amount_total:sum'],
                ['currency_id']
            )
            total = 0.0
            for g in groups:
                if g['currency_id']:
                    currency = self.env['res.currency'].browse(g['currency_id'][0])
                    total += currency._convert(
                        g['amount_total'],
                        company_currency,
                        self.env.company,
                        today
                    )
            return total

        total_revenue_mtd = _get_total(month_start)
        total_revenue_ytd = _get_total(year_start)

        groups = SaleOrder.read_group(
            [('state', '=', 'sale')],
            ['amount_total:sum', 'id:count'],
            ['currency_id']
        )

        total_revenue = 0.0
        total_orders = 0
        for g in groups:
            if g['currency_id']:
                currency = self.env['res.currency'].browse(g['currency_id'][0])
                total_revenue += currency._convert(
                    g['amount_total'],
                    company_currency,
                    self.env.company,
                    today
                )
                total_orders += g.get('currency_id_count', 0)

        avg_order_value = total_revenue / total_orders if total_orders else 0

        sales_info = {
            'sale_orders': sale_orders,
            'quotation': quotations,
            'orders_to_invoice': orders_to_invoice,
            'orders_fully_invoiced': orders_fully_invoiced,
            'conversion_rate': conversion_rate,
            'total_revenue_mtd': company_currency.format(total_revenue_mtd),
            'total_revenue_ytd': company_currency.format(total_revenue_ytd),
            'avg_order_value': company_currency.format(avg_order_value),
        }

        nvrc_domain = build_domain([('state', 'in', ['sale', 'done'])], "nvrc_filter")

        date_from, date_to = None, None
        for d in nvrc_domain:
            if d[0] == 'date_order' and d[1] == '>=':
                date_from = d[2]
            elif d[0] == 'date_order' and d[1] == '<=':
                date_to = d[2]

        if date_from and isinstance(date_from, str):
            date_from = fields.Date.from_string(date_from)
        if date_to and isinstance(date_to, str):
            date_to = fields.Date.from_string(date_to)

        current_customers = self.read_group(
            nvrc_domain, ['partner_id'], ['partner_id']
        )
        customer_ids = [rec['partner_id'][0] for rec in current_customers if rec['partner_id']]

        new_customers, returning_customers = [], []
        if customer_ids:
            first_orders = self.read_group(
                [('partner_id', 'in', customer_ids), ('state', 'in', ['sale', 'done'])],
                ['partner_id', 'date_order:min'],
                ['partner_id']
            )
            first_order_map = {rec['partner_id'][0]: rec['date_order'] for rec in first_orders if rec['partner_id']}

            partners = self.env['res.partner'].browse(customer_ids)
            for partner in partners:
                first_date = first_order_map.get(partner.id)
                if first_date and date_from and first_date.date() >= date_from:
                    new_customers.append({'id': partner.id, 'name': partner.display_name})
                else:
                    returning_customers.append({'id': partner.id, 'name': partner.display_name})

        new_vs_returning = {
            'summary': {
                'labels': ["New Customers", "Returning Customers"],
                'values': [len(new_customers), len(returning_customers)],
            },
            'details': {
                'new': new_customers[:limit],
                'returning': returning_customers[:limit],
            }
        }

        return {
            'sales_by_team': teams,
            'sales_by_person': persons,
            'top_customers': customers,
            'top_products': top_products,
            'lowest_products': low_products,
            'overdue_customers': overdue_customers,
            'order_status': order_status,
            'invoice_status': invoice_status,
            'product_categories': product_categories,
            'sales_info': sales_info,
            'new_vs_returning': new_vs_returning,
        }