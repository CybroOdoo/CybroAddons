# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import io
import logging

from odoo.tests import tagged, TransactionCase


try:
    import openpyxl
except ImportError:
    openpyxl = None

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_reporting')
class TestWmPrintableReports(TransactionCase):
    """Unit tests verifying pricing rule summary and billing report PDF generation."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        # Fixtures for Route Sheet
        cls.point = cls.env['wm.collection.point'].create({'name': 'Print Point 1'})
        cls.route = cls.env['wm.route'].create({
            'name': 'ROUTE-PRINT-001',
            'date': '2026-07-28',
        })
        cls.route_line = cls.env['wm.route.line'].create({
            'route_id': cls.route.id,
            'collection_point_id': cls.point.id,
            'sequence': 1,
        })

        # Fixtures for Inspection Checklist
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Inspect Brand'})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.env['fleet.vehicle.model'].create({'name': 'Inspect Model', 'brand_id': brand.id}).id,
            'license_plate': 'WM-INSPECT-01',
        })
        cls.item = cls.env['wm.checklist.item'].create({'name': 'Tire Pressure Check', 'checklist_type': 'pre_trip'})
        cls.checklist = cls.env['wm.vehicle.maintenance.checklist'].create({
            'name': 'CHK-PRINT-001',
            'vehicle_id': cls.vehicle.id,
            'checklist_type': 'pre_trip',
            'state': 'checked',
        })
        cls.chk_line = cls.env['wm.checklist.line'].create({
            'checklist_id': cls.checklist.id,
            'item_id': cls.item.id,
            'is_passed': True,
        })

        # Fixtures for Pricing Rule
        cls.category = cls.env['wm.waste.category'].create({'name': 'Print Category'})
        cls.pricing_rule = cls.env['wm.pricing.rule'].create({
            'name': 'Standard Tariff',
            'waste_category_id': cls.category.id,
            'price_per_kg': 5.0,
            'min_weight': 50.0,
            'min_charge': 250.0,
        })

    def test_route_sheet_pdf_rendering(self):
        """
        Test that route sheet pdf rendering behaves as expected.
        """
        report_action = self.env.ref('wm_collection.action_report_route_sheet')
        pdf_content, content_type = report_action._render_qweb_pdf(report_action, res_ids=[self.route.id])
        self.assertTrue(pdf_content, "Route sheet QWeb PDF should render content without error")
        self.assertIn(content_type, ['pdf', 'html'])
        _logger.info('PASS: test_route_sheet_pdf_rendering')

    def test_vehicle_inspection_checklist_pdf_rendering(self):
        """
        Test that vehicle inspection checklist pdf rendering behaves as
        expected.
        """
        report_action = self.env.ref('wm_collection.action_report_vehicle_inspection_checklist')
        pdf_content, content_type = report_action._render_qweb_pdf(report_action, res_ids=[self.checklist.id])
        self.assertTrue(pdf_content, "Vehicle inspection checklist QWeb PDF should render content without error")
        self.assertIn(content_type, ['pdf', 'html'])
        _logger.info('PASS: test_vehicle_inspection_checklist_pdf_rendering')

    def test_pricing_rule_summary_pdf_rendering(self):
        """
        Test that pricing rule summary pdf rendering behaves as expected.
        """
        report_action = self.env.ref('wm_contracts_billing.action_report_pricing_rule_summary')
        pdf_content, content_type = report_action._render_qweb_pdf(report_action, res_ids=[self.pricing_rule.id])
        self.assertTrue(pdf_content, "Pricing rule summary QWeb PDF should render content without error")
        self.assertIn(content_type, ['pdf', 'html'])
        _logger.info('PASS: test_pricing_rule_summary_pdf_rendering')

    def test_pricing_rule_summary_xlsx_openpyxl_roundtrip(self):
        """
        Test that pricing rule summary xlsx openpyxl roundtrip behaves as
        expected.
        """
        if not openpyxl:
            self.skipTest("openpyxl is not installed")

        wizard = self.env['wm.pricing.rule.summary.wizard'].create({
            'output_type': 'xlsx',
            'rule_ids': [(6, 0, [self.pricing_rule.id])],
        })
        wizard.action_generate_report()
        self.assertTrue(wizard.data_file, "XLSX file binary data should be generated")

        import base64
        file_data = base64.b64decode(wizard.data_file)
        wb = openpyxl.load_workbook(io.BytesIO(file_data))
        ws = wb.active

        self.assertEqual(ws.title, "Pricing Rule Summary")
        cell_val = ws.cell(row=2, column=1).value
        self.assertEqual(cell_val, self.category.name, "Generated XLSX should contain category name in row 2 cell 1")
        _logger.info('PASS: test_pricing_rule_summary_xlsx_openpyxl_roundtrip')
