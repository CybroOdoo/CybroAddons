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
from odoo.exceptions import UserError

class TestStockPicking(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product SP',
            'type': 'consu',
        })
        cls.picking_type = cls.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
        
        cls.measure = cls.env['quality.measure'].create({
            'name': 'Test Measure SP',
            'type': 'quantity',
            'product_id': cls.product.id,
            'picking_type_ids': [(4, cls.picking_type.id)],
        })
        
        cls.partner = cls.env['res.partner'].create({'name': 'SP Partner'})
        cls.picking = cls.env['stock.picking'].create({
            'partner_id': cls.partner.id,
            'picking_type_id': cls.picking_type.id,
            'location_id': cls.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': cls.env.ref('stock.stock_location_stock').id,
        })
        
        cls.move = cls.env['stock.move'].create({
            'name': cls.product.name,
            'product_id': cls.product.id,
            'product_uom_qty': 10,
            'product_uom': cls.product.uom_id.id,
            'picking_id': cls.picking.id,
            'location_id': cls.picking.location_id.id,
            'location_dest_id': cls.picking.location_dest_id.id,
        })

    def test_01_generate_quality_alert_and_compute(self):
        """Test generate_quality_alert and computing alert counts."""
        self.picking.generate_quality_alert()
        # Trigger compute
        self.picking._compute_quality_alert()
        self.assertEqual(self.picking.alert_count, 1, "Alert count should be 1")
        self.assertTrue(self.picking.alert_ids, "Alert IDs should be populated")

    def test_02_action_confirm(self):
        """Test that confirming picking automatically generates alert."""
        # Unlink any existing alerts from test_01 since transaction might roll back or not
        self.env['quality.alert'].search([('picking_id', '=', self.picking.id)]).unlink()
        
        self.picking.action_confirm()
        self.picking._compute_quality_alert()
        self.assertTrue(self.picking.alert_count > 0, "Alert should be auto-generated on confirm")

    def test_03_action_quality_alert(self):
        """Test action dictionary returned for quality alert."""
        self.picking.generate_quality_alert()
        action = self.picking.action_quality_alert()
        self.assertIsInstance(action, dict, "Action should return a dict")
        self.assertTrue('res_id' in action or 'domain' in action, "Action should have domain or res_id")

    def test_04_action_done_validation(self):
        """Test that _action_done prevents validation if alert is fail or wait."""
        # Generate an alert
        self.picking.generate_quality_alert()
        alert = self.env['quality.alert'].search([('picking_id', '=', self.picking.id)], limit=1)
        
        alert.final_status = 'wait'
        with self.assertRaises(UserError):
            self.picking._action_done()
            
        alert.final_status = 'fail'
        with self.assertRaises(UserError):
            self.picking._action_done()
            
        alert.final_status = 'pass'
        try:
            self.picking._action_done()
        except UserError as e:
            self.assertNotIn('quality test', str(e).lower(), "Should not raise quality test errors if passed")
