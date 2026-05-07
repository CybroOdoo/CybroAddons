# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prasudhi A (odoo@cybrosys.com)
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
###############################################################################
from odoo.tests.common import TransactionCase
from unittest.mock import patch, MagicMock
from odoo.addons.website_order_delivery_tracking.controllers.website_order_delivery_tracking import Tracking

class TestTrackingDelivery(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = Tracking()

        # Create a product for the delivery carrier
        cls.product = cls.env['product.product'].create({
            'name': 'Test Delivery Product',
            'type': 'service',
        })

        # Create a delivery carrier
        cls.delivery_carrier = cls.env['delivery.carrier'].create({
            'name': 'Test Carrier',
            'fixed_price': 5.0,
            'product_id': cls.product.id,
        })
        
        # Create a partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })
        
        # Create picking type
        cls.picking_type = cls.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('company_id', '=', cls.env.company.id)
        ], limit=1)
        
        # Create a stock picking record
        cls.picking = cls.env['stock.picking'].create({
            'partner_id': cls.partner.id,
            'picking_type_id': cls.picking_type.id,
            'location_id': cls.picking_type.default_location_src_id.id or cls.env.ref('stock.stock_location_stock').id,
            'location_dest_id': cls.picking_type.default_location_dest_id.id or cls.env.ref('stock.stock_location_customers').id,
            'carrier_id': cls.delivery_carrier.id,
            'carrier_tracking_ref': 'TRK-12345',
            'tracking_status': 'In Transit'
        })
        
        # Create another stock picking record without status
        cls.picking_no_status = cls.env['stock.picking'].create({
            'partner_id': cls.partner.id,
            'picking_type_id': cls.picking_type.id,
            'location_id': cls.picking_type.default_location_src_id.id or cls.env.ref('stock.stock_location_stock').id,
            'location_dest_id': cls.picking_type.default_location_dest_id.id or cls.env.ref('stock.stock_location_customers').id,
            'carrier_id': cls.delivery_carrier.id,
            'carrier_tracking_ref': 'TRK-67890',
        })

    def test_01_res_config_settings_api_key(self):
        """Test API Key can be set via res.config.settings"""
        self.env['ir.config_parameter'].sudo().set_param(
            'website_order_delivery_tracking.delivery_tracking_api_key', 'test_key_123'
        )
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'website_order_delivery_tracking.delivery_tracking_api_key'
        )
        self.assertEqual(api_key, 'test_key_123', 'API key should match the configured value')

    def test_02_get_track_details(self):
        """Test rendering tracking template"""
        mock_request = MagicMock()
        with patch('odoo.addons.website_order_delivery_tracking.controllers.website_order_delivery_tracking.request', new=mock_request):
            mock_request.env = self.env
            mock_request.render.return_value = 'Mock Response'
            
            result = self.controller.get_track_details()
            # If it returns a response object, check its data
            if hasattr(result, 'data'):
                self.assertEqual(result.data.decode(), 'Mock Response')
            else:
                self.assertEqual(result, 'Mock Response')
            mock_request.render.assert_called_once_with('website_order_delivery_tracking.trackingTemplate')

    def test_03_input_data_processing(self):
        """Test fetching input json data sent from js"""
        mock_request = MagicMock()
        with patch('odoo.addons.website_order_delivery_tracking.controllers.website_order_delivery_tracking.request', new=mock_request):
            mock_request.env = self.env
            
            # Test with status present
            result = self.controller.input_data_processing(input_data='TRK-12345')
            self.assertEqual(len(result), 1, 'Should return tracking details for 1 picking')
            self.assertEqual(result[0][0], self.picking.name)
            self.assertEqual(result[0][2], 'Test Carrier')
            self.assertEqual(result[0][3], 'In Transit')
            
            # Test with status absent
            result2 = self.controller.input_data_processing(input_data='TRK-67890')
            self.assertEqual(len(result2), 1)
            self.assertEqual(result2[0][3], 'Status currently not available')
            
            # Test unknown tracking ref
            result3 = self.controller.input_data_processing(input_data='UNKNOWN')
            self.assertEqual(len(result3), 0)

    def test_04_track_data_edit_success(self):
        """Test track data edit with correct api key"""
        mock_request = MagicMock()
        with patch('odoo.addons.website_order_delivery_tracking.controllers.website_order_delivery_tracking.request', new=mock_request):
            mock_request.env = self.env
            
            self.env['ir.config_parameter'].sudo().set_param(
                'website_order_delivery_tracking.delivery_tracking_api_key', 'ValidApiKey123'
            )
            
            post_data = {
                'tracking_number': 'TRK-12345',
                'api_key': 'ValidApiKey123',
                'tracking_status': 'Delivered'
            }
            
            # Check initial status is not Delivered
            self.assertNotEqual(self.picking.tracking_status, 'Delivered')
            
            response = self.controller.track_data_edit(**post_data)
            
            self.assertEqual(response, 'Delivered')
            self.picking.invalidate_recordset(['tracking_status'])
            self.assertEqual(self.picking.tracking_status, 'Delivered')

    def test_05_track_data_edit_invalid_key(self):
        """Test track data edit with invalid api key"""
        mock_request = MagicMock()
        with patch('odoo.addons.website_order_delivery_tracking.controllers.website_order_delivery_tracking.request', new=mock_request):
            mock_request.env = self.env
            
            self.env['ir.config_parameter'].sudo().set_param(
                'website_order_delivery_tracking.delivery_tracking_api_key', 'ValidApiKey123'
            )
            
            post_data = {
                'tracking_number': 'TRK-12345',
                'api_key': 'WrongApiKey',
                'tracking_status': 'Returned'
            }
            
            initial_status = self.picking.tracking_status
            
            response = self.controller.track_data_edit(**post_data)
            
            self.assertEqual(response, [])
            self.picking.invalidate_recordset(['tracking_status'])
            self.assertEqual(self.picking.tracking_status, initial_status, 'Status should not have changed')

    def test_06_track_data_edit_invalid_tracking(self):
        """Test track data edit with invalid tracking number but correct api key"""
        mock_request = MagicMock()
        with patch('odoo.addons.website_order_delivery_tracking.controllers.website_order_delivery_tracking.request', new=mock_request):
            mock_request.env = self.env
            
            self.env['ir.config_parameter'].sudo().set_param(
                'website_order_delivery_tracking.delivery_tracking_api_key', 'ValidApiKey123'
            )
            
            post_data = {
                'tracking_number': 'NONEXISTENT_TRK',
                'api_key': 'ValidApiKey123',
                'tracking_status': 'In Transit'
            }
            
            response = self.controller.track_data_edit(**post_data)
            
            self.assertEqual(response, [])
