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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import io
import json
from datetime import timedelta

from openpyxl import load_workbook

from odoo import Command, fields
from odoo.exceptions import ValidationError
from odoo.tests import HttpCase, TransactionCase, new_test_user
from odoo.tools import json_default


class FakeResponse:
    """Stand-in for the HTTP response the XLSX reports write to."""

    def __init__(self):
        self.stream = io.BytesIO()


class TestSaleReportAdvanced(TransactionCase):
    """Run every report as a real sales user, like the wizard buttons do."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(
            cls.env, login='report_user',
            groups='sales_team.group_sale_salesman_all_leads,'
                   'account.group_account_invoice')
        cls.partner = cls.env['res.partner'].create({'name': 'Report Buyer'})
        cls.other = cls.env['res.partner'].create({'name': 'Other Buyer'})
        cls.category = cls.env['product.category'].create({'name': 'Report'})
        taxes = cls.env['account.tax'].create([
            {'name': 'Tax A', 'amount': 5.0},
            {'name': 'Tax B', 'amount': 10.0},
        ])
        cls.product = cls.env['product.product'].create({
            'name': 'Report Product', 'list_price': 100.0,
            'standard_price': 60.0, 'categ_id': cls.category.id,
            'taxes_id': [Command.set(taxes.ids)],
        })
        cls.free = cls.env['product.product'].create({
            'name': 'Zero Cost', 'list_price': 10.0, 'standard_price': 0.0,
            'categ_id': cls.category.id, 'taxes_id': [Command.clear()],
        })
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'date_order': fields.Datetime.now().replace(hour=9),
            'order_line': [
                Command.create({'product_id': cls.product.id,
                                'product_uom_qty': 2}),
                Command.create({'product_id': cls.free.id,
                                'product_uom_qty': 1}),
                Command.create({'display_type': 'line_note',
                                'name': 'A note'}),
            ],
        })
        cls.order.action_confirm()
        cls.order.date_order = fields.Datetime.now().replace(hour=9)
        cls.env['sale.order.line'].flush_model()
        cls.order.order_line.filtered('product_id').write(
            {'qty_delivered': 2})
        cls.invoice = cls.order._create_invoices()
        cls.invoice.action_post()
        cls.today = fields.Date.today()

    def _wizard(self, model, vals):
        return self.env[model].with_user(self.user).create(vals)

    def _run(self, wizard, pdf_method, xlsx_method):
        """Press both buttons, and render what the buttons return."""
        action = getattr(wizard, pdf_method)()
        # The web client gets the action as JSON
        data = json.loads(json.dumps(action['data'], default=json_default))
        report = self.env['ir.actions.report'].with_user(self.user)
        html = report._render_qweb_html(action['report_name'], [], data=data)[0]
        action = getattr(wizard, xlsx_method)()
        self.assertEqual(action['report_type'], 'xlsx')
        response = FakeResponse()
        wizard.get_xlsx_report(action['data']['options'], response)
        self.assertTrue(load_workbook(io.BytesIO(response.stream.getvalue())))
        return html.decode()

    def test_product_profit_by_customer(self):
        html = self._run(self._wizard('sale.report.advance', {
            'type': 'customer',
            'customer_ids': [Command.set(self.partner.ids)],
        }), 'action_get_report', 'action_get_excel_report')
        self.assertIn(self.order.name, html)

    def test_total_margin_is_the_margin_of_the_totals(self):
        """Cost 60 and profit 40 + 10 give 83.33, not a sum of percentages."""
        wizard = self._wizard('sale.report.advance', {
            'type': 'customer',
            'customer_ids': [Command.set(self.partner.ids)],
        })
        html = self._run(wizard, 'action_get_report',
                         'action_get_excel_report')
        self.assertRegex(html, r'Total margin:</span>\s*83\.33\s')
        response = FakeResponse()
        wizard.get_xlsx_report(
            wizard.action_get_excel_report()['data']['options'], response)
        sheet = load_workbook(io.BytesIO(response.stream.getvalue())).active
        values = [cell.value for row in sheet.rows for cell in row]
        self.assertIn(83.33, values)

    def test_product_profit_by_product(self):
        html = self._run(self._wizard('sale.report.advance', {
            'type': 'product',
            'product_ids': [Command.set(self.product.ids)],
        }), 'action_get_report', 'action_get_excel_report')
        self.assertIn(self.order.name, html)

    def test_product_profit_by_both(self):
        html = self._run(self._wizard('sale.report.advance', {
            'type': 'both',
            'customer_ids': [Command.set(self.partner.ids)],
            'product_ids': [Command.set(self.product.ids)],
        }), 'action_get_report', 'action_get_excel_report')
        self.assertIn(self.order.name, html)

    def test_product_profit_by_dates(self):
        html = self._run(self._wizard('sale.report.advance', {
            'from_date': self.today - timedelta(days=1),
            'to_date': self.today + timedelta(days=1),
        }), 'action_get_report', 'action_get_excel_report')
        self.assertIn(self.order.name, html)

    def test_invoice_analysis_each_status(self):
        for status in ('open', 'both'):
            html = self._run(self._wizard('sale.report.invoice', {
                'customer_ids': [Command.set(self.partner.ids)],
                'status': status,
                'company_ids': [Command.set(self.env.company.ids)],
            }), 'action_get_invoice_report', 'action_get_excel_invoice_report')
            self.assertIn(self.invoice.name, html)

    def test_invoice_analysis_without_paid_invoices(self):
        wizard = self._wizard('sale.report.invoice', {
            'customer_ids': [Command.set(self.partner.ids)],
            'status': 'paid',
        })
        with self.assertRaises(ValidationError):
            wizard.action_get_invoice_report()

    def test_category_report(self):
        html = self._run(self._wizard('sale.report.category', {
            'category_ids': [Command.set(self.category.ids)],
            'from_date': self.today - timedelta(days=1),
            'to_date': self.today + timedelta(days=1),
            'company_ids': [Command.set(self.env.company.ids)],
        }), 'action_get_category_report', 'action_get_excel_category_report')
        self.assertIn(self.order.name, html)

    def test_tax_is_the_rounded_amount_of_the_line(self):
        wizard = self._wizard('sale.report.category', {
            'category_ids': [Command.set(self.category.ids)],
        })
        line = self.order.order_line.filtered(
            lambda rec: rec.product_id == self.product)
        rows = wizard._get_data()['form']
        row = next(rec for rec in rows if rec['product_id'] == self.product.name)
        self.assertEqual(row['tax'], round(line.price_tax, 2))
        self.assertEqual(row['total'], round(line.price_total, 2))

    def test_category_report_keeps_all_filters(self):
        wizard = self._wizard('sale.report.category', {
            'category_ids': [Command.set(self.category.ids)],
            'from_date': self.today - timedelta(days=9),
            'to_date': self.today - timedelta(days=5),
        })
        with self.assertRaises(ValidationError):
            wizard.action_get_category_report()

    def test_indent_report(self):
        html = self._run(self._wizard('sale.report.indent', {
            'customer_ids': [Command.set(self.partner.ids)],
            'category_ids': [Command.set(self.category.ids)],
            'status': 'sale',
        }), 'action_get_indent_report', 'action_get_excel_indent_report')
        self.assertIn('Report Product', html)

    def test_indent_status_is_exact(self):
        wizard = self._wizard('sale.report.indent', {
            'customer_ids': [Command.set(self.partner.ids)],
            'category_ids': [Command.set(self.category.ids)],
            'status': 'draft',
        })
        with self.assertRaises(ValidationError):
            wizard.action_get_indent_report()

    def test_analysis_by_sale_order(self):
        html = self._run(self._wizard('sale.report.analysis', {
            'customer_ids': [Command.set(self.partner.ids)],
            'print_type': 'sale',
        }), 'action_get_analysis_report', 'action_get_excel_analysis_report')
        self.assertIn(self.order.name, html)

    def test_analysis_by_product(self):
        html = self._run(self._wizard('sale.report.analysis', {
            'customer_ids': [Command.set(self.partner.ids)],
            'product_ids': [Command.set(self.product.ids)],
            'print_type': 'product',
            'status': 'sale',
            'from_date': self.today - timedelta(days=1),
        }), 'action_get_analysis_report', 'action_get_excel_analysis_report')
        self.assertIn(self.order.name, html)

    def test_hourly_report(self):
        html = self._run(self._wizard('sale.report.weekly', {
            'date': self.today,
            'invoice_status': self.order.invoice_status,
        }), 'action_get_weekly_report', 'action_get_excel_weekly_report')
        self.assertIn(self.order.name, html)
        self.assertIn('Morning (05:00-12:00)', html)

    def test_two_customers_in_one_report(self):
        order = self.order.copy({'partner_id': self.other.id})
        order.action_confirm()
        partners = self.partner | self.other
        categories = self.category
        html = self._run(self._wizard('sale.report.advance', {
            'type': 'customer', 'customer_ids': [Command.set(partners.ids)],
        }), 'action_get_report', 'action_get_excel_report')
        self.assertIn(order.name, html)
        self._run(self._wizard('sale.report.indent', {
            'customer_ids': [Command.set(partners.ids)],
            'category_ids': [Command.set(categories.ids)],
        }), 'action_get_indent_report', 'action_get_excel_indent_report')
        self._run(self._wizard('sale.report.analysis', {
            'customer_ids': [Command.set(partners.ids)],
        }), 'action_get_analysis_report', 'action_get_excel_analysis_report')

    def test_report_menu_is_reachable(self):
        """The Sales app holds the menus of the reports."""
        self.assertTrue(self.env.ref('sale.sale_menu_root').active)
        menu = self.env.ref('sale_report_advanced.sale_advanced_report_menu')
        self.assertTrue(menu.active)

    def test_date_range_is_validated(self):
        for model, vals in (
            ('sale.report.category',
             {'category_ids': [Command.set(self.category.ids)]}),
            ('sale.report.indent',
             {'category_ids': [Command.set(self.category.ids)],
              'customer_ids': [Command.set(self.partner.ids)]}),
            ('sale.report.analysis',
             {'customer_ids': [Command.set(self.partner.ids)]}),
        ):
            with self.assertRaises(ValidationError):
                self._wizard(model, dict(
                    vals, from_date=self.today,
                    to_date=self.today - timedelta(days=1)))


class TestXlsxRoute(HttpCase):
    """Test the download route of the XLSX reports."""

    def _post(self, model):
        self.authenticate('admin', 'admin')
        return self.url_open('/xlsx_reports', data={
            'model': model,
            'report_name': 'Hourly',
            'options': json.dumps({
                'times': {'noon': 'Noon'}, 'type': 'total',
                'form': [{'order': 'S1', 'date': '2026-01-01', 'amount': 5.0,
                          'time': 'noon'}],
            }),
            'csrf_token': self.csrf_token(),
        })

    def test_download(self):
        response = self._post('sale.report.weekly')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(load_workbook(io.BytesIO(response.content)))
        self.assertIn('Hourly.xlsx', response.headers['Content-Disposition'])

    def test_other_models_are_refused(self):
        self.assertEqual(self._post('res.partner').status_code, 404)
