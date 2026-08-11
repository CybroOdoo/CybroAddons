# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestPosSession(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.booking_product = cls.env.ref(
            "table_reservation_on_website.product_product_table_booking"
        )

    def test_get_pos_ui_product_product_appends_booking_product(self):
        session = self.env["pos.session"]
        params = {"search_params": {"fields": ["name", "default_code", "categ_id"]}}

        with patch(
            "odoo.addons.point_of_sale.models.pos_session.PosSession._get_pos_ui_product_product",
            create=True,
            return_value=[{"id": 99, "name": "Existing Product"}],
        ):
            result = session._get_pos_ui_product_product(params)

        appended = result[-1]
        self.assertEqual(appended["id"], self.booking_product.id)
        self.assertEqual(appended["name"], self.booking_product.name)
        self.assertEqual(appended["default_code"], self.booking_product.default_code)
        self.assertEqual(appended["categ"]["id"], self.booking_product.categ_id.id)
