# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import date, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """Extend sale.order to provide data for the Sales Dashboard."""

    _inherit = "sale.order"

    @api.model
    def _get_range(self, filter_key, custom_start=None, custom_end=None):
        """Return the start and end dates for the selected filter."""
        today = fields.Date.context_today(self)

        if filter_key == "this_week":
            start = today - timedelta(days=today.weekday())
            return start, min(start + timedelta(days=6), today)

        if filter_key == "this_month":
            return today.replace(day=1), today

        if filter_key == "this_year":
            return today.replace(month=1, day=1), today

        if filter_key == "custom":
            if not custom_start or not custom_end:
                return None, None

            custom_start = fields.Date.to_date(custom_start)
            custom_end = fields.Date.to_date(custom_end)

            if custom_end < custom_start:
                raise UserError(_("Please select a valid date range."))

            return custom_start, custom_end

        return None, None

    @api.model
    def _get_filter_key(self, filters, specific_filter_key):
        """Resolve the effective filter for an individual dashboard section."""
        global_filter = filters.get("global_filter", "this_week")

        if global_filter == "custom":
            return "custom"

        if global_filter == "select_period":
            return filters.get(specific_filter_key, "this_week")

        return global_filter

    @api.model
    def _build_dashboard_domain(
        self,
        base_domain,
        filters,
        specific_filter_key,
        date_field="date_order",
    ):
        """Build a domain using the global or section-specific date filter."""
        filter_key = self._get_filter_key(filters, specific_filter_key)

        custom_start = custom_end = None
        if filter_key == "custom":
            custom_range = filters.get("custom_range") or {}
            custom_start = custom_range.get("from")
            custom_end = custom_range.get("to")

        date_from, date_to = self._get_range(
            filter_key,
            custom_start,
            custom_end,
        )

        domain = list(base_domain)
        if date_from:
            domain.append((date_field, ">=", date_from))
        if date_to:
            domain.append((date_field, "<=", date_to))

        return domain

    @api.model
    def _build_global_domain(self, base_domain, filters, date_field="date_order"):
        """Build a domain using the global dashboard date filter."""
        filters = filters or {}
        return self._build_dashboard_domain(
            base_domain,
            filters,
            "global_filter",
            date_field,
        )

    @api.model
    def get_tile_domain(self, base_domain, filters=None):
        """Return a date-filtered domain for dashboard tile navigation."""
        return self._build_global_domain(base_domain, filters or {})

    @api.model
    def get_sales_dashboard_data(self, filters=None):
        """Return all data required by the Sales Dashboard."""
        filters = filters or {}

        try:
            limit = int(filters.get("limit", 10))
        except (TypeError, ValueError):
            limit = 10

        limit = max(1, min(limit, 100))

        SaleOrder = self.env["sale.order"]
        SaleLine = self.env["sale.order.line"]
        AccountMove = self.env["account.move"]

        # ---------------------------------------------------------
        # Sales by team
        # ---------------------------------------------------------
        team_domain = self._build_dashboard_domain(
            [("state", "in", ["sale", "done"])],
            filters,
            "team_filter",
        )
        sales_by_team_grouped = SaleOrder._read_group(
            team_domain,
            groupby=["team_id"],
            aggregates=["amount_total:sum"],
            limit=limit,
            order="amount_total:sum desc",
        )

        sales_by_team = [
            {
                "id": team.id,
                "name": team.display_name,
                "amount": amount,
            }
            for team, amount in sales_by_team_grouped
            if team
        ]

        # ---------------------------------------------------------
        # Sales by salesperson
        # ---------------------------------------------------------
        person_domain = self._build_dashboard_domain(
            [("state", "in", ["sale", "done"])],
            filters,
            "person_filter",
        )
        sales_by_person_grouped = SaleOrder._read_group(
            person_domain,
            groupby=["user_id"],
            aggregates=["amount_total:sum"],
            limit=limit,
            order="amount_total:sum desc",
        )

        sales_by_person = [
            {
                "id": user.id,
                "name": user.display_name,
                "amount": amount,
            }
            for user, amount in sales_by_person_grouped
            if user
        ]

        # ---------------------------------------------------------
        # Top customers
        # ---------------------------------------------------------
        customer_domain = self._build_dashboard_domain(
            [("state", "in", ["sale", "done"])],
            filters,
            "customer_filter",
        )
        customers_grouped = SaleOrder._read_group(
            customer_domain,
            groupby=["partner_id"],
            aggregates=["amount_total:sum"],
            limit=limit,
            order="amount_total:sum desc",
        )

        top_customers = [
            {
                "id": partner.id,
                "name": partner.display_name,
                "amount": amount,
            }
            for partner, amount in customers_grouped
            if partner
        ]

        # ---------------------------------------------------------
        # Top-selling products
        # ---------------------------------------------------------
        product_domain = self._build_dashboard_domain(
            [("order_id.state", "in", ["sale", "done"])],
            filters,
            "product_filter",
            "order_id.date_order",
        )

        product_category_id = filters.get("product_category_id")
        if product_category_id:
            product_domain.append(
                ("product_id.categ_id", "=", int(product_category_id))
            )

        top_products_grouped = SaleLine._read_group(
            product_domain,
            groupby=["product_id"],
            aggregates=["product_uom_qty:sum"],
            limit=limit,
            order="product_uom_qty:sum desc",
        )

        top_products = [
            {
                "id": product.id,
                "name": product.display_name,
                "quantity": quantity,
            }
            for product, quantity in top_products_grouped
            if product
        ]

        # ---------------------------------------------------------
        # Least-selling products
        # ---------------------------------------------------------
        low_product_domain = self._build_dashboard_domain(
            [("order_id.state", "in", ["sale", "done"])],
            filters,
            "low_product_filter",
            "order_id.date_order",
        )

        low_product_category_id = filters.get("low_product_category_id")
        if low_product_category_id:
            low_product_domain.append(
                ("product_id.categ_id", "=", int(low_product_category_id))
            )

        low_products_grouped = SaleLine._read_group(
            low_product_domain,
            groupby=["product_id"],
            aggregates=["product_uom_qty:sum"],
            limit=limit,
            order="product_uom_qty:sum asc",
        )

        lowest_products = [
            {
                "id": product.id,
                "name": product.display_name,
                "quantity": quantity,
            }
            for product, quantity in low_products_grouped
            if product
        ]

        # ---------------------------------------------------------
        # Order status
        # ---------------------------------------------------------
        order_domain = self._build_dashboard_domain(
            [],
            filters,
            "order_filter",
        )
        order_status_grouped = SaleOrder._read_group(
            order_domain,
            groupby=["state"],
            aggregates=["__count"],
        )

        order_status_labels = {
            "draft": _("Quotation"),
            "sent": _("Quotation Sent"),
            "sale": _("Sales Order"),
            "done": _("Locked"),
            "cancel": _("Cancelled"),
        }

        order_status = [
            {
                "status": order_status_labels.get(
                    state,
                    state.capitalize() if state else "",
                ),
                "count": count,
            }
            for state, count in order_status_grouped
        ]

        # ---------------------------------------------------------
        # Invoice status
        # ---------------------------------------------------------
        invoice_domain = self._build_dashboard_domain(
            [("move_type", "=", "out_invoice")],
            filters,
            "invoice_filter",
            "invoice_date",
        )
        invoice_status_grouped = AccountMove._read_group(
            invoice_domain,
            groupby=["state"],
            aggregates=["__count"],
        )

        invoice_status_labels = {
            "draft": _("Draft"),
            "posted": _("Posted"),
            "cancel": _("Cancelled"),
        }

        invoice_status = [
            {
                "status": invoice_status_labels.get(
                    state,
                    state.capitalize() if state else "",
                ),
                "count": count,
            }
            for state, count in invoice_status_grouped
        ]

        # ---------------------------------------------------------
        # Overdue customers
        # ---------------------------------------------------------
        today = fields.Date.context_today(self)

        overdue_domain = self._build_dashboard_domain(
            [
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("invoice_date_due", "<", today),
                ("amount_residual", ">", 0),
            ],
            filters,
            "overdue_filter",
            "invoice_date",
        )

        overdue_grouped = AccountMove._read_group(
            overdue_domain,
            groupby=["partner_id"],
            aggregates=["amount_residual:sum"],
            limit=limit,
            order="amount_residual:sum desc",
        )

        overdue_customers = [
            {
                "id": partner.id,
                "name": partner.display_name,
                "amount": amount,
            }
            for partner, amount in overdue_grouped
            if partner
        ]

        # ---------------------------------------------------------
        # Product categories
        # ---------------------------------------------------------
        categories = self.env["product.category"].search([])
        product_categories = [
            {
                "id": category.id,
                "name": category.display_name,
            }
            for category in categories
        ]

        # ---------------------------------------------------------
        # Dashboard sales tiles
        # ---------------------------------------------------------
        sale_orders_domain = self._build_dashboard_domain(
            [("state", "in", ["sale", "done"])],
            filters,
            "order_tile_filter",
        )
        sale_orders = SaleOrder.search_count(sale_orders_domain)

        quotations_domain = self._build_dashboard_domain(
            [("state", "in", ["draft", "sent"])],
            filters,
            "quotation_tile_filter",
        )
        quotations = SaleOrder.search_count(quotations_domain)

        to_invoice_domain = self._build_dashboard_domain(
            [("invoice_status", "=", "to invoice")],
            filters,
            "to_invoice_tile_filter",
        )
        orders_to_invoice = SaleOrder.search_count(to_invoice_domain)

        invoiced_domain = self._build_dashboard_domain(
            [("invoice_status", "=", "invoiced")],
            filters,
            "invoiced_tile_filter",
        )
        orders_fully_invoiced = SaleOrder.search_count(invoiced_domain)

        conversion_total = sale_orders + quotations
        conversion_rate = round(
            sale_orders / conversion_total * 100
            if conversion_total
            else 0
        )

        # ---------------------------------------------------------
        # Revenue summary
        # ---------------------------------------------------------
        company = self.env.company
        company_currency = company.currency_id
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)

        def get_converted_revenue(start_date):
            groups = SaleOrder._read_group(
                domain=[
                    ("state", "=", "sale"),
                    ("date_order", ">=", start_date),
                    ("date_order", "<=", fields.Datetime.now()),
                ],
                groupby=["currency_id"],
                aggregates=["amount_total:sum"],
            )

            total = 0.0
            for currency, amount_total in groups:
                if currency:
                    total += currency._convert(
                        amount_total,
                        company_currency,
                        company,
                        today,
                    )
            return total

        total_revenue_mtd = get_converted_revenue(month_start)
        total_revenue_ytd = get_converted_revenue(year_start)

        revenue_groups = SaleOrder._read_group(
            domain=[("state", "=", "sale")],
            groupby=["currency_id"],
            aggregates=["amount_total:sum", "__count"],
        )

        total_revenue = 0.0
        total_orders = 0

        for currency, amount_total, order_count in revenue_groups:
            if currency:
                total_revenue += currency._convert(
                    amount_total,
                    company_currency,
                    company,
                    today,
                )
                total_orders += order_count

        average_order_value = (
            total_revenue / total_orders if total_orders else 0.0
        )

        sales_info = {
            "sale_orders": sale_orders,
            "quotation": quotations,
            "orders_to_invoice": orders_to_invoice,
            "orders_fully_invoiced": orders_fully_invoiced,
            "conversion_rate": conversion_rate,
            "total_revenue_mtd": company_currency.format(
                total_revenue_mtd
            ),
            "total_revenue_ytd": company_currency.format(
                total_revenue_ytd
            ),
            "avg_order_value": company_currency.format(
                average_order_value
            ),
        }

        # ---------------------------------------------------------
        # New vs. returning customers
        # ---------------------------------------------------------
        nvrc_domain = self._build_dashboard_domain(
            [("state", "in", ["sale", "done"])],
            filters,
            "nvrc_filter",
        )

        date_from = next(
            (
                domain_item[2]
                for domain_item in nvrc_domain
                if domain_item[0] == "date_order"
                and domain_item[1] == ">="
            ),
            None,
        )

        if date_from:
            date_from = fields.Date.to_date(date_from)

        current_customers = SaleOrder._read_group(
            nvrc_domain,
            groupby=["partner_id"],
            aggregates=[],
        )

        customer_ids = [
            partner.id
            for partner, in current_customers
            if partner
        ]

        new_customers = []
        returning_customers = []

        if customer_ids:
            first_orders = SaleOrder._read_group(
                domain=[
                    ("partner_id", "in", customer_ids),
                    ("state", "in", ["sale", "done"]),
                ],
                groupby=["partner_id"],
                aggregates=["date_order:min"],
            )

            first_order_map = {
                partner.id: first_order_date
                for partner, first_order_date in first_orders
                if partner
            }

            partners = self.env["res.partner"].browse(customer_ids)

            for partner in partners:
                first_order_date = first_order_map.get(partner.id)
                first_order_day = (
                    fields.Date.to_date(first_order_date)
                    if first_order_date
                    else None
                )

                customer_data = {
                    "id": partner.id,
                    "name": partner.display_name,
                }

                if (
                    first_order_day
                    and date_from
                    and first_order_day >= date_from
                ):
                    new_customers.append(customer_data)
                else:
                    returning_customers.append(customer_data)

        new_vs_returning = {
            "summary": {
                "labels": [
                    _("New Customers"),
                    _("Returning Customers"),
                ],
                "values": [
                    len(new_customers),
                    len(returning_customers),
                ],
            },
            "details": {
                "new": new_customers[:limit],
                "returning": returning_customers[:limit],
            },
        }

        return {
            "sales_by_team": sales_by_team,
            "sales_by_person": sales_by_person,
            "top_customers": top_customers,
            "top_products": top_products,
            "lowest_products": lowest_products,
            "overdue_customers": overdue_customers,
            "order_status": order_status,
            "invoice_status": invoice_status,
            "product_categories": product_categories,
            "sales_info": sales_info,
            "new_vs_returning": new_vs_returning,
        }