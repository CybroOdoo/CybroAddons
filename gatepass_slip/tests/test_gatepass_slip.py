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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestGatepassSlip(TransactionCase):
    """Test suite for Delivery Gate Pass module functionality and report generation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country = cls.env['res.country'].search([], limit=1)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Gatepass Test Customer',
            'street': '742 Evergreen Terrace',
            'city': 'Springfield',
            'zip': '97477',
            'country_id': cls.country.id if cls.country else False,
        })
        cls.warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.env.company.id)], limit=1)
        if not cls.warehouse:
            cls.warehouse = cls.env['stock.warehouse'].create({
                'name': 'Gatepass Test Warehouse',
                'code': 'GTWH',
                'company_id': cls.env.company.id,
            })
        cls.picking_type_out = cls.warehouse.out_type_id
        cls.location_src = cls.picking_type_out.default_location_src_id
        cls.location_dest = cls.picking_type_out.default_location_dest_id

        cls.product = cls.env['product.product'].create({
            'name': 'Gatepass Cargo Product',
            'type': 'consu',
        })

        cls.picking = cls.env['stock.picking'].create({
            'partner_id': cls.partner.id,
            'picking_type_id': cls.picking_type_out.id,
            'location_id': cls.location_src.id,
            'location_dest_id': cls.location_dest.id,
            'vehicle_no': 'KA-01-GP-9999',
            'vehicle_driver_name': 'Alex Mercer',
            'driver_contact_number': '+1-555-0199',
            'corresponding_company': 'Apex Logistics LLC',
            'is_enable_order_line': True,
        })

        cls.move = cls.env['stock.move'].create({
            'product_id': cls.product.id,
            'product_uom_qty': 15.0,
            'picking_id': cls.picking.id,
            'location_id': cls.location_src.id,
            'location_dest_id': cls.location_dest.id,
        })

        cls.report = cls.env.ref('gatepass_slip.action_generate_gatepass')

    def test_01_stock_picking_gatepass_fields(self):
        """Verify delivery order gate pass fields creation, defaults, and updates."""
        self.assertEqual(self.picking.vehicle_no, 'KA-01-GP-9999')
        self.assertEqual(self.picking.vehicle_driver_name, 'Alex Mercer')
        self.assertEqual(self.picking.driver_contact_number, '+1-555-0199')
        self.assertEqual(self.picking.corresponding_company, 'Apex Logistics LLC')
        self.assertTrue(self.picking.is_enable_order_line)

        self.picking.write({
            'vehicle_no': 'DL-04-TR-1234',
            'is_enable_order_line': False,
        })
        self.assertEqual(self.picking.vehicle_no, 'DL-04-TR-1234')
        self.assertFalse(self.picking.is_enable_order_line)

    def test_02_report_gatepass_html_with_order_lines(self):
        """Verify Gate Pass report HTML generation includes order line details."""
        self.picking.write({'is_enable_order_line': True})
        html_content, _ = self.report._render_qweb_html(self.report.id, [self.picking.id])
        self.assertTrue(html_content)
        self.assertIn(b'GATE PASS', html_content)
        self.assertIn(b'Alex Mercer', html_content)
        self.assertIn(b'KA-01-GP-9999', html_content)
        self.assertIn(b'+1-555-0199', html_content)
        self.assertIn(b'Apex Logistics LLC', html_content)
        self.assertIn(b'PRODUCT DETAILS', html_content)
        self.assertIn(b'Gatepass Cargo Product', html_content)

    def test_03_report_gatepass_html_without_order_lines(self):
        """Verify Gate Pass report HTML generation excludes product details when disabled."""
        self.picking.write({'is_enable_order_line': False})
        html_content, _ = self.report._render_qweb_html(self.report.id, [self.picking.id])
        self.assertTrue(html_content)
        self.assertIn(b'GATE PASS', html_content)
        self.assertIn(b'Alex Mercer', html_content)
        self.assertNotIn(b'PRODUCT DETAILS', html_content)

    def test_04_report_action_dictionary(self):
        """Verify report_action returns valid ir.actions.report dictionary."""
        action = self.report.report_action(self.picking, config=False)
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_name'), 'gatepass_slip.report_gatepass_slip')
        self.assertEqual(action.get('report_type'), 'qweb-pdf')

    def test_05_multi_picking_report(self):
        """Verify Gate Pass report generation with multiple pickings."""
        second_picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
            'vehicle_no': 'MH-12-PQ-5678',
            'vehicle_driver_name': 'David Miller',
            'is_enable_order_line': False,
        })
        html_content, _ = self.report._render_qweb_html(
            self.report.id,
            [self.picking.id, second_picking.id],
        )
        self.assertTrue(html_content)
        self.assertIn(b'Alex Mercer', html_content)
        self.assertIn(b'David Miller', html_content)
        self.assertIn(b'MH-12-PQ-5678', html_content)

    def test_06_report_minimal_empty_fields(self):
        """Verify report generation with minimal fields without partner or driver."""
        minimal_picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
        })
        html_content, _ = self.report._render_qweb_html(self.report.id, [minimal_picking.id])
        self.assertTrue(html_content)
        self.assertIn(b'GATE PASS', html_content)
