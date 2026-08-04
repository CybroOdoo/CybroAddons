# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.info)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestDynamicPurchaseReport(TransactionCase):

    def setUp(self):
        super(TestDynamicPurchaseReport, self).setUp()
        # SQL workaround to drop NOT NULL constraints for fields added by external
        # modules (purchase_stock, website_sale) that are not in dependencies.
        table_fields = {
            'res_partner': ['group_rfq', 'group_on'],
            'product_template': ['publish_date', 'base_unit_count'],
            'product_product': ['base_unit_count'],
            'purchase_order': ['picking_type_id'],
        }
        for table, fields in table_fields.items():
            for field in fields:
                self.env.cr.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name=%s AND column_name=%s", (table, field)
                )
                if self.env.cr.fetchone():
                    self.env.cr.execute(
                        f"ALTER TABLE {table} ALTER COLUMN {field} DROP NOT NULL"
                    )

        self.dynamic_purchase_report = self.env['dynamic.purchase.report']
        self.partner = self.env['res.partner'].create({
            'name': 'Test Vendor',
        })

        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'list_price': 100.0,
        })
        self.purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'name': self.product.name,
                    'product_id': self.product.id,
                    'product_qty': 5.0,
                    'product_uom_id': self.product.uom_id.id,
                    'price_unit': 100.0,
                    'date_planned': '2026-05-22',
                })
            ],
        })
        self.purchase_order.button_confirm()

    def test_01_dynamic_purchase_report_creation(self):
        """Test the creation of the dynamic purchase report record and basic functionality."""
        report = self.dynamic_purchase_report.create({
            'report_type': 'report_by_order',
        })
        self.assertTrue(report.id, "Dynamic purchase report record not created.")
        
        # Test report_by_order
        res = getattr(self.dynamic_purchase_report, 'purchase_report')([report.id])
        self.assertEqual(res.get('type'), 'ir.actions.client', "Report should return a client action.")
        self.assertEqual(res.get('name'), 'Purchase Orders', "Report name should be 'Purchase Orders'.")
        
        filters = res.get('filters')
        self.assertIn('report_type', filters, "Filters should contain report_type.")
        self.assertEqual(filters['report_type'], 'Report By Order', "Report type filter is incorrect.")
        
        lines = res.get('report_lines')
        self.assertTrue(isinstance(lines, list), "Report lines should be a list.")

    def test_02_report_by_product(self):
        """Test the report execution for 'report_by_product' type."""
        report = self.dynamic_purchase_report.create({
            'report_type': 'report_by_product',
        })
        res = getattr(self.dynamic_purchase_report, 'purchase_report')([report.id])
        self.assertEqual(res.get('filters', {}).get('report_type'), 'Report By Product')
        
    def test_03_report_by_state(self):
        """Test the report execution for 'report_by_state' type."""
        report = self.dynamic_purchase_report.create({
            'report_type': 'report_by_state',
        })
        res = getattr(self.dynamic_purchase_report, 'purchase_report')([report.id])
        self.assertEqual(res.get('filters', {}).get('report_type'), 'Report By State')

    def test_04_get_filter(self):
        """Test the get_filter method directly."""
        report = self.dynamic_purchase_report.create({
            'report_type': 'report_by_categories',
        })
        filters = self.dynamic_purchase_report.get_filter([report.id])
        self.assertEqual(filters.get('report_type'), 'Report By Categories')
