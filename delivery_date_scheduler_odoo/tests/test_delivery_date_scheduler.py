# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Surya Gayathry TA (odoo@cybrosys.com)
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
#############################################################################
import json
from datetime import date, timedelta
from odoo.tests import common


class TestDeliveryDateScheduler(common.HttpCase):
    """Test cases for checking the delivery date scheduler portal routes."""

    @classmethod
    def setUpClass(cls):
        super(TestDeliveryDateScheduler, cls).setUpClass()
        # Create a dedicated test user for authentication
        cls.user_login = 'test_scheduler_user'
        cls.user_password = 'test_password_123'
        cls.test_user = cls.env['res.users'].create({
            'name': 'Test Scheduler User',
            'login': cls.user_login,
            'password': cls.user_password,
        })
        
        # Create partner and product for the sale order
        cls.partner = cls.test_user.partner_id
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100.0,
        })

    def setUp(self):
        super(TestDeliveryDateScheduler, self).setUp()
        # Create a Sale Order for testing
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        # Authenticate as the dedicated test user
        self.authenticate(self.user_login, self.user_password)

    def test_01_delivery_date_schedule_validation(self):
        """Test the delivery date validation logic through the portal route."""
        
        # Scenario A: Warning/Restriction disabled
        self.env['ir.config_parameter'].sudo().set_param(
            'delivery_date_scheduler_odoo.warning_date', False)
        
        payload = {'params': {'date': '2026-05-10'}}
        response = self.url_open(
            '/delivery_date_schedule',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        result = json.loads(response.content).get('result')
        self.assertEqual(result.get('error_value'), 3,
                         "Should return error_value 3 when warning_date is disabled")

        # Scenario B: Warning enabled, date within range
        self.env['ir.config_parameter'].sudo().set_param(
            'delivery_date_scheduler_odoo.warning_date', True)
        self.env['ir.config_parameter'].sudo().set_param(
            'delivery_date_scheduler_odoo.min_date_range', 2)
        self.env['ir.config_parameter'].sudo().set_param(
            'delivery_date_scheduler_odoo.max_date_range', 10)
        
        # Date within range (today + 5 days)
        test_date_within = (date.today() + timedelta(days=5)).strftime('%Y-%m-%d')
        payload['params']['date'] = test_date_within
        response = self.url_open(
            '/delivery_date_schedule',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        result = json.loads(response.content).get('result')
        self.assertEqual(result.get('error_value'), 1,
                         "Should return error_value 1 when date is within range")

        # Scenario C: Warning enabled, date outside range
        # Date outside range (today + 15 days)
        test_date_outside = (date.today() + timedelta(days=15)).strftime('%Y-%m-%d')
        payload['params']['date'] = test_date_outside
        response = self.url_open(
            '/delivery_date_schedule',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        result = json.loads(response.content).get('result')
        self.assertEqual(result.get('error_value'), 2,
                         "Should return error_value 2 when date is outside range")

    def test_02_confirm_delivery_date_schedule(self):
        """Test the order confirmation route from the portal."""
        
        test_date = (date.today() + timedelta(days=5)).strftime('%Y-%m-%d')
        test_description = "Please deliver between 9 AM and 5 PM."
        
        payload = {
            'params': {
                'id': self.sale_order.id,
                'date': test_date,
                'description': test_description
            }
        }
        
        response = self.url_open(
            '/confirm_delivery_date_schedule',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 200, "Route should return 200 OK")
        
        # Verify the Sale Order updates
        self.sale_order.invalidate_recordset()
        self.assertEqual(self.sale_order.state, 'sale',
                         "Order should be confirmed ('sale' state)")
        self.assertEqual(str(self.sale_order.commitment_date.date()), test_date,
                         "Commitment date should be updated correctly")
        self.assertEqual(self.sale_order.user_description, test_description,
                         "User description should be updated correctly")
