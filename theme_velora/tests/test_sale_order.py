# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleOrderAvataxCompat(TransactionCase):
    """Test suite for theme_velora SaleOrderAvataxCompat model extension."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Velora Customer',
        })
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })

    def test_is_avatax_field_value(self):
        """Verify is_avatax computed field always returns False."""
        self.assertFalse(
            self.order.is_avatax,
            "is_avatax should evaluate to False by default."
        )

    def test_compute_is_avatax_compat_execution(self):
        """Explicitly execute compute method and assert order.is_avatax."""
        self.order._compute_is_avatax_compat()
        self.assertFalse(
            self.order.is_avatax,
            "is_avatax must remain False after recomputing."
        )

    def test_is_avatax_multiple_records(self):
        """Verify compute handles multiple sale order records in recordset."""
        order_2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        orders = self.order | order_2
        orders._compute_is_avatax_compat()
        for order in orders:
            self.assertFalse(order.is_avatax)
