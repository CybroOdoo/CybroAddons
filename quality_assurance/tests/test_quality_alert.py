# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase

class TestQualityAlert(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({'name': 'Test Product QA'})
        cls.picking_type = cls.env['stock.picking.type'].search([], limit=1)
        
        cls.measure = cls.env['quality.measure'].create({
            'name': 'Test Measure QA',
            'type': 'quantity',
            'product_id': cls.product.id,
            'picking_type_ids': [(4, cls.picking_type.id)],
        })
        
        cls.partner = cls.env['res.partner'].create({'name': 'QA Partner'})
        cls.picking = cls.env['stock.picking'].create({
            'partner_id': cls.partner.id,
            'picking_type_id': cls.picking_type.id,
            'location_id': cls.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': cls.env.ref('stock.stock_location_stock').id,
        })

    def test_01_create_sequence(self):
        """Test that default 'New' name is replaced by a sequence on creation."""
        alert = self.env['quality.alert'].create({'product_id': self.product.id})
        self.assertNotEqual(alert.name, 'New', "Name should be overridden by sequence")
        self.assertTrue(alert.name, "Name sequence should not be empty")

    def test_02_action_generate_tests(self):
        """Test generating tests based on measures."""
        alert = self.env['quality.alert'].create({
            'product_id': self.product.id,
            'picking_id': self.picking.id,
        })
        alert.action_generate_tests()
        self.assertTrue(alert.tests, "Tests should be generated")
        self.assertEqual(alert.tests[0].quality_measure_id.id, self.measure.id)

    def test_03_compute_final_status(self):
        """Test final status computation based on test results."""
        alert = self.env['quality.alert'].create({'product_id': self.product.id})
        
        # No tests -> wait
        alert._compute_final_status()
        self.assertEqual(alert.final_status, 'wait', "Status should be wait if no tests")
        
        # Test passes -> pass
        test = self.env['quality.test'].create({
            'quality_measure_id': self.measure.id,
            'alert_id': alert.id,
            'test_status': 'pass',
        })
        alert._compute_final_status()
        self.assertEqual(alert.final_status, 'pass', "Status should be pass if all passed")
        
        # Test fails -> fail
        test.test_status = 'fail'
        alert._compute_final_status()
        self.assertEqual(alert.final_status, 'fail', "Status should be fail if one fails")
