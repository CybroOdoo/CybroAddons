# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha (odoo@cybrosys.com)
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
###############################################################################
import odoo.tests

@odoo.tests.common.tagged('post_install', '-at_install')
class TestCallForPriceWebsite(odoo.tests.HttpCase):
    def setUp(self):
        super(TestCallForPriceWebsite, self).setUp()
        self.product = self.env['product.template'].create({
            'name': 'Test Product Website',
            'is_published': True,
            'price_call': True,
        })

    def test_call_for_price_submit(self):
        data = {
            'first_name': 'Web',
            'last_name': 'Test',
            'email': 'web@example.com',
            'phone': '987654321',
            'quantity': '3',
            'message': 'Hello from web',
            'product_id': str(self.product.id),
        }
        
        response = self.url_open('/call_for_price/submit', data=data)
        
        self.assertEqual(response.status_code, 200, "Should return 200 OK")
        
        record = self.env['call.price'].search([('email', '=', 'web@example.com')], limit=1)
        self.assertTrue(record, "The call price record should be created")
        self.assertEqual(record.first_name, 'Web')
        self.assertEqual(record.product_id.id, self.product.id)
        self.assertEqual(record.quantity, 3)
