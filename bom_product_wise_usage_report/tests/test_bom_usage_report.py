# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1) It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE,ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from datetime import date, timedelta
from odoo.exceptions import ValidationError
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestBomUsageReport(common.TransactionCase):
    """Test suite for BOM Product Wise Usage Report."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        layout = cls.env.ref('web.external_layout_standard', raise_if_not_found=False)
        if layout:
            cls.company.external_report_layout_id = layout.id

        # Units of measure
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.uom_meter = cls.env.ref('uom.product_uom_meter')
        cls.uom_kg = cls.env.ref('uom.product_uom_kgm')

        # Parent / Finished products
        cls.finished_product = cls.env['product.product'].create({
            'name': 'Bicycle Test',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
        })

        # Component products with distinct UoMs
        cls.component_meter = cls.env['product.product'].create({
            'name': 'Steel Pipe Test',
            'type': 'consu',
            'uom_id': cls.uom_meter.id,
        })
        cls.component_kg = cls.env['product.product'].create({
            'name': 'Chemical Powder Test',
            'type': 'consu',
            'uom_id': cls.uom_kg.id,
        })

        # Locations (search or create to avoid relying on demo data)
        cls.stock_location = cls.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('company_id', 'in', [False, cls.company.id]),
        ], limit=1)
        if not cls.stock_location:
            cls.stock_location = cls.env['stock.location'].create({
                'name': 'Stock Location Test',
                'usage': 'internal',
                'company_id': cls.company.id,
            })

        cls.production_location = cls.env['stock.location'].search([
            ('usage', '=', 'production'),
            ('company_id', 'in', [False, cls.company.id]),
        ], limit=1)
        if not cls.production_location:
            cls.production_location = cls.env['stock.location'].create({
                'name': 'Production Location Test',
                'usage': 'production',
                'company_id': cls.company.id,
            })

    def test_01_wizard_defaults(self):
        """Test default wizard field values."""
        wizard = self.env['bom.usage.details'].create({})
        self.assertEqual(wizard.to_date, date.today())
        self.assertFalse(wizard.from_date)
        self.assertFalse(wizard.un_build_orders)

    def test_02_date_validation_from_after_to(self):
        """Test that from_date after to_date raises ValidationError."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        wizard = self.env['bom.usage.details'].create({
            'from_date': today,
            'to_date': yesterday,
        })
        with self.assertRaises(ValidationError):
            wizard.action_get_report()

    def test_03_same_day_date_allowed(self):
        """Test that same-day report (from_date == to_date) passes date validation."""
        today = date.today()
        wizard = self.env['bom.usage.details'].create({
            'from_date': today,
            'to_date': today,
            'product_ids': [(6, 0, [self.component_meter.id])],
        })
        # If no moves exist, it should raise "No data is available" instead of date ValidationError
        with self.assertRaises(ValidationError) as cm:
            wizard.action_get_report()
        self.assertIn("No data is available", str(cm.exception))

    def test_04_component_uom_and_fractional_qty_in_report(self):
        """Test that component UoM is used (not parent UoM) and fractional qty (< 1) is kept."""
        today = date.today()

        # Create manufacturing order
        mo = self.env['mrp.production'].create({
            'product_id': self.finished_product.id,
            'product_qty': 1.0,
            'uom_id': self.uom_unit.id,
            'company_id': self.company.id,
            'date_finished': today,
            'state': 'done',
        })

        # Component 1: 2.5 Meters of Steel Pipe
        self.env['stock.move'].create({
            'product_id': self.component_meter.id,
            'uom_id': self.uom_meter.id,
            'product_uom_qty': 2.5,
            'raw_material_production_id': mo.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.production_location.id,
            'state': 'done',
            'company_id': self.company.id,
        })

        # Component 2: Fractional 0.5 Kg of Chemical Powder (qty < 1)
        self.env['stock.move'].create({
            'product_id': self.component_kg.id,
            'uom_id': self.uom_kg.id,
            'product_uom_qty': 0.5,
            'raw_material_production_id': mo.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.production_location.id,
            'state': 'done',
            'company_id': self.company.id,
        })

        wizard = self.env['bom.usage.details'].create({
            'from_date': today,
            'to_date': today,
            'product_ids': [(6, 0, [self.component_meter.id, self.component_kg.id])],
        })

        action = wizard.action_get_report()
        self.assertEqual(action.get('type'), 'ir.actions.report')
        report_data = action.get('data', {})
        body = report_data.get('body', [])

        # Both components must be present in body
        child_pids = [entry['child_product_id'] for entry in body]
        self.assertIn(self.component_meter.id, child_pids)
        self.assertIn(self.component_kg.id, child_pids)

        for entry in body:
            if entry['child_product_id'] == self.component_meter.id:
                # Must be 2.5 Meters, NOT 2.5 Units
                self.assertEqual(entry['child_quantity_used'], 2.5)
                self.assertEqual(entry['uom'], self.uom_meter.name)
            elif entry['child_product_id'] == self.component_kg.id:
                # Fractional qty 0.5 kg must not be dropped
                self.assertEqual(entry['child_quantity_used'], 0.5)
                self.assertEqual(entry['uom'], self.uom_kg.name)

    def test_05_unbuild_order_company_isolation(self):
        """Test that unbuild orders from another company do not deduct quantities."""
        today = date.today()
        other_company = self.env['res.company'].create({'name': 'Second Company Test'})
        other_stock_loc = self.env['stock.location'].create({
            'name': 'Other Stock',
            'usage': 'internal',
            'company_id': other_company.id,
        })
        other_prod_loc = self.env['stock.location'].create({
            'name': 'Other Prod',
            'usage': 'production',
            'company_id': other_company.id,
        })

        # MO in primary company: 5.0 Meters used
        mo = self.env['mrp.production'].create({
            'product_id': self.finished_product.id,
            'product_qty': 1.0,
            'uom_id': self.uom_unit.id,
            'company_id': self.company.id,
            'date_finished': today,
            'state': 'done',
        })
        self.env['stock.move'].create({
            'product_id': self.component_meter.id,
            'uom_id': self.uom_meter.id,
            'product_uom_qty': 5.0,
            'raw_material_production_id': mo.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.production_location.id,
            'state': 'done',
            'company_id': self.company.id,
        })

        # Unbuild in other company for the same product: 3.0 Meters
        unbuild_other = self.env['mrp.unbuild'].create({
            'product_id': self.finished_product.id,
            'product_qty': 1.0,
            'uom_id': self.uom_unit.id,
            'company_id': other_company.id,
            'state': 'done',
        })
        self.env['stock.move'].create({
            'product_id': self.component_meter.id,
            'uom_id': self.uom_meter.id,
            'product_uom_qty': 3.0,
            'unbuild_id': unbuild_other.id,
            'location_id': other_prod_loc.id,
            'location_dest_id': other_stock_loc.id,
            'state': 'done',
            'company_id': other_company.id,
        })

        wizard = self.env['bom.usage.details'].create({
            'from_date': today,
            'to_date': today,
            'product_ids': [(6, 0, [self.component_meter.id])],
            'un_build_orders': True,
        })

        action = wizard.action_get_report()
        body = action.get('data', {}).get('body', [])
        meter_entry = [e for e in body if e['child_product_id'] == self.component_meter.id]
        self.assertTrue(meter_entry)
        # Quantity should still be 5.0, NOT 2.0 (5.0 - 3.0) because unbuild was in other company
        self.assertEqual(meter_entry[0]['child_quantity_used'], 5.0)
