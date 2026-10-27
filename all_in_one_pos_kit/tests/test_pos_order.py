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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosOrderDashboard(TransactionCase):


    def test_dashboard_methods_return_empty_data_shapes(self):
        pos_order = self.env["pos.order"]

        self.assertEqual(pos_order.get_department("pos_hourly_sales")[2], "HOURS")
        self.assertEqual(pos_order.get_department("pos_monthly_sales")[2], "DAYS")
        self.assertEqual(pos_order.get_department("pos_yearly_sales")[2], "MONTHS")
        self.assertIn("payment_details", pos_order.get_details())
        self.assertIn("total_sale", pos_order.get_refund_details())
        for result in (
                pos_order.get_the_top_customer(),
                pos_order.get_the_top_products(),
                pos_order.get_the_top_categories()):
            self.assertEqual(len(result), 2)
            self.assertIsInstance(result[0], list)
            self.assertIsInstance(result[1], list)

    def test_invoice_number_empty_without_posted_invoice(self):
        order = self.env["pos.order"].new({})
        order._compute_invoice_number()
        self.assertFalse(order.invoice_number)
