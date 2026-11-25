# -*- coding: utf-8 -*-
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import Command, fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestThermalInvoiceReport(TransactionCase):
    """Unit test suite for Thermal Invoice Report module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        # Ensure company has details set for report header
        cls.company.write({
            'company_details': 'Test Company Details\n123 Test Street',
        })

        # Create a test customer partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer Partner',
            'email': 'customer@test.com',
            'street': 'Test Street 456',
        })

        # Create a test product
        cls.product = cls.env['product.product'].create({
            'name': 'Test Thermal Product',
            'list_price': 100.0,
            'type': 'consu',
        })

        # Create a customer invoice with both product and description-only lines
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [
                Command.create({
                    'product_id': cls.product.id,
                    'name': 'Test Thermal Product Line',
                    'quantity': 2.0,
                    'price_unit': 100.0,
                    'discount': 10.0,
                }),
                Command.create({
                    'name': 'Custom Line Without Product',
                    'quantity': 1.0,
                    'price_unit': 30.0,
                    'discount': 0.0,
                }),
            ],
        })

        # Create a second customer invoice for multi-recordset tests
        cls.invoice_2 = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [
                Command.create({
                    'product_id': cls.product.id,
                    'name': 'Test Second Product Line',
                    'quantity': 1.0,
                    'price_unit': 50.0,
                    'discount': 0.0,
                }),
            ],
        })

    def test_01_module_is_installed(self):
        """Verify thermal_invoice_report module is installed."""
        module = self.env['ir.module.module'].search([('name', '=', 'thermal_invoice_report')], limit=1)
        self.assertTrue(module, "Module thermal_invoice_report must be registered.")
        self.assertEqual(module.state, 'installed', "Module thermal_invoice_report should be in installed state.")

    def test_02_paperformat_configuration(self):
        """Verify thermal paperformat definition and parameters."""
        paperformat = self.env.ref('thermal_invoice_report.paperformat_thermal_paper', raise_if_not_found=False)
        self.assertTrue(paperformat, "Paper format 'thermal_invoice_report.paperformat_thermal_paper' must exist.")
        self.assertEqual(paperformat.format, 'custom', "Paper format must be 'custom'.")
        self.assertEqual(paperformat.page_width, 58, "Paper width should be 58mm.")
        self.assertEqual(paperformat.page_height, 75, "Paper height should be 75mm.")
        self.assertEqual(paperformat.orientation, 'Portrait', "Orientation should be Portrait.")
        self.assertEqual(paperformat.margin_top, 1, "Top margin should be 1mm.")
        self.assertEqual(paperformat.margin_bottom, 0, "Bottom margin should be 0mm.")
        self.assertEqual(paperformat.margin_left, 0, "Left margin should be 0mm.")
        self.assertEqual(paperformat.margin_right, 0, "Right margin should be 0mm.")

    def test_03_report_action_definition(self):
        """Verify report action exists and is correctly configured."""
        report_action = self.env.ref('thermal_invoice_report.report_print_thermal_so_action', raise_if_not_found=False)
        self.assertTrue(report_action, "Report action 'thermal_invoice_report.report_print_thermal_so_action' must exist.")
        self.assertEqual(report_action.model, 'account.move', "Report model must be 'account.move'.")
        self.assertEqual(report_action.report_type, 'qweb-pdf', "Report type must be 'qweb-pdf'.")
        self.assertEqual(report_action.report_name, 'thermal_invoice_report.report_thermal', "Report name must match template ID.")
        self.assertEqual(report_action.binding_model_id.model, 'account.move', "Report should be bound to account.move model.")
        self.assertEqual(report_action.binding_type, 'report', "Binding type must be 'report'.")
        self.assertEqual(
            report_action.paperformat_id,
            self.env.ref('thermal_invoice_report.paperformat_thermal_paper'),
            "Paperformat must link to paperformat_thermal_paper.",
        )

    def test_04_render_thermal_invoice_html(self):
        """Verify QWeb HTML rendering of single thermal invoice report."""
        report_name = 'thermal_invoice_report.report_thermal'
        html_content, _ = self.env['ir.actions.report']._render_qweb_html(report_name, [self.invoice.id])
        self.assertTrue(html_content, "Generated HTML report content should not be empty.")
        decoded_html = html_content.decode('utf-8')
        self.assertIn('thermal-report-page', decoded_html, "HTML should contain thermal-report-page class.")
        self.assertIn(self.partner.name, decoded_html, "HTML should contain customer name.")
        self.assertIn('Test Thermal Product Line', decoded_html, "Invoice line with product should be present.")
        self.assertIn('Custom Line Without Product', decoded_html, "Invoice line without product should be present.")

    def test_05_render_multi_invoices(self):
        """Verify QWeb report rendering for multiple invoices (multi-recordset support)."""
        report_name = 'thermal_invoice_report.report_thermal'
        invoice_ids = [self.invoice.id, self.invoice_2.id]
        html_content, _ = self.env['ir.actions.report']._render_qweb_html(report_name, invoice_ids)
        self.assertTrue(html_content, "Generated HTML content for multiple invoices should not be empty.")
        decoded_html = html_content.decode('utf-8')
        self.assertIn('Test Thermal Product', decoded_html, "First invoice product should be present.")
        self.assertIn('Test Second Product Line', decoded_html, "Second invoice line should be present.")

    def test_06_render_thermal_invoice_report_action(self):
        """Verify report action execution via _render_qweb_pdf."""
        report_action = self.env.ref('thermal_invoice_report.report_print_thermal_so_action')
        content, _ = self.env['ir.actions.report']._render_qweb_pdf(
            report_action, res_ids=self.invoice.ids
        )
        self.assertTrue(content, "Report content should be successfully generated.")
