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
from odoo.tests.common import TransactionCase

class TestCallPrice(TransactionCase):
    def setUp(self):
        super(TestCallPrice, self).setUp()
        self.product = self.env['product.template'].create({
            'name': 'Test Product'
        })
        self.call_price = self.env['call.price'].create({
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'phone': '1234567890',
            'product_id': self.product.id,
            'quantity': 2,
            'message': 'Test Message'
        })

    def test_action_done(self):
        self.call_price.action_done()
        self.assertEqual(self.call_price.state, 'done', 'State should be done')

    def test_action_cancel(self):
        self.call_price.action_cancel()
        self.assertEqual(self.call_price.state, 'cancel', 'State should be cancel')

    def test_create_form(self):
        self.env['call.price'].create_form(
            'First', 'Last', self.product.id, '123', 'email@test.com', 'Msg', 5
        )
        record = self.env['call.price'].search([('email', '=', 'email@test.com')], limit=1)
        self.assertTrue(record, 'Record should be created via create_form')
        self.assertEqual(record.first_name, 'First')
        self.assertEqual(record.quantity, 5)
