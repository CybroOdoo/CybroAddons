# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
class TestSaleReturn(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })

        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })

        cls.return_order = cls.env['sale.return'].create({
            'sale_order_id': cls.sale_order.id,
            'partner_id': cls.partner.id,
        })

    def test_sale_return_sequence(self):
        """Test return sequence."""

        self.assertTrue(
            self.return_order.name
        )

    def test_partner_return_count(self):
        """Test partner return count."""

        self.partner._compute_return_order_count()

        self.assertEqual(
            self.partner.return_order_count,
            1
        )

    def test_sale_order_return_count(self):
        """Test order return count."""

        self.sale_order._compute_return_order_count()

        self.assertEqual(
            self.sale_order.return_order_count,
            1
        )

    def test_partner_return_action(self):
        """Test partner return action."""

        action = self.partner.action_open_returns()

        self.assertEqual(
            action['res_model'],
            'sale.return'
        )

    def test_sale_order_return_action(self):
        """Test order return action."""

        action = self.sale_order.action_open_returns()

        self.assertEqual(
            action['res_model'],
            'sale.return'
        )

    def test_return_cancel(self):
        """Test return cancellation."""

        self.return_order.action_return_cancel()

        self.assertEqual(
            self.return_order.state,
            'cancel'
        )

    def test_access_url(self):
        """Test access url."""

        self.return_order._compute_access_url()

        self.assertIn(
            '/my/return_orders/',
            self.return_order.access_url
        )

    def test_report_filename(self):
        """Test report filename."""

        self.assertEqual(
            self.return_order._get_report_base_filename(),
            f'Sale Return - {self.return_order.name}'
        )