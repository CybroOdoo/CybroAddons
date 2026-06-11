# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosOrder(TransactionCase):
    """Test customer screen rating fields on pos.order."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Customer Screen Partner',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Customer Screen Product',
            'available_in_pos': True,
            'list_price': 50.0,
        })
        cls.payment_method = cls.env['pos.payment.method'].create({
            'name': 'Customer Screen Cash',
        })
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Customer Screen Order POS Config',
            'payment_method_ids': [(4, cls.payment_method.id)],
        })
        cls.pos_config.open_ui()
        cls.pos_session = cls.pos_config.current_session_id

    def test_pos_order_has_rating_defaults(self):
        """POS order has customer screen rating fields."""
        order = self._create_pos_order('Order 0002')

        self.assertEqual(order.rating, '5')
        self.assertFalse(order.rating_text)

    def test_pos_order_write_updates_rating_from_review(self):
        """Writing a POS order applies the review linked by POS reference."""
        order = self._create_pos_order('Order 0003')
        self.env['pos.order.review'].create({
            'review_text': 'Needs faster billing',
            'review_star': 'star2',
            'pos_session': self.pos_session.id,
            'partner': self.partner.id,
            'pos_order_ref': 'Order 0003',
        })

        order.write({'rating_text': 'Trigger review sync'})

        self.assertEqual(order.rating, '2')
        self.assertEqual(order.rating_text, 'Needs faster billing')

    def _create_pos_order(self, pos_reference):
        """Create a minimal POS order for rating tests."""
        return self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'partner_id': self.partner.id,
            'pos_reference': pos_reference,
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'qty': 1,
                'price_unit': 50.0,
                'price_subtotal': 50.0,
                'price_subtotal_incl': 50.0,
            })],
            'amount_total': 50.0,
            'amount_tax': 0.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
        })
