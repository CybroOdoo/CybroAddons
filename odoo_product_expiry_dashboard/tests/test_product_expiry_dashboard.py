# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################

from datetime import datetime, time, timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProductExpiryDashboard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref("stock.stock_location_stock")

        cls.food_category = cls.env["product.category"].create({
            "name": "Expiry Test Food",
        })
        cls.medicine_category = cls.env["product.category"].create({
            "name": "Expiry Test Medicine",
        })

        cls.product_yogurt = cls.env["product.product"].create({
            "name": "Expiry Yogurt",
            "type": "product",
            "tracking": "lot",
            "categ_id": cls.food_category.id,
            "use_expiration_date": True,
        })
        cls.product_juice = cls.env["product.product"].create({
            "name": "Expiry Juice",
            "type": "product",
            "tracking": "lot",
            "categ_id": cls.food_category.id,
            "use_expiration_date": True,
        })
        cls.product_vaccine = cls.env["product.product"].create({
            "name": "Expiry Vaccine",
            "type": "product",
            "tracking": "lot",
            "categ_id": cls.medicine_category.id,
            "use_expiration_date": True,
        })

        cls.lot_today = cls._create_lot(cls.product_yogurt, "LOT-TODAY", 0, 2)
        cls.lot_one_day = cls._create_lot(cls.product_yogurt, "LOT-ONE", 1, 3)
        cls.lot_seven_day = cls._create_lot(cls.product_juice, "LOT-FIVE", 5, 4)
        cls.lot_thirty_day = cls._create_lot(cls.product_juice, "LOT-TEN", 10, 5)
        cls.lot_one_twenty_day = cls._create_lot(cls.product_vaccine, "LOT-SIXTY", 60, 6)
        cls.lot_expired_yogurt = cls._create_lot(cls.product_yogurt, "LOT-EXP-YOG", -2, 7)
        cls.lot_expired_vaccine = cls._create_lot(cls.product_vaccine, "LOT-EXP-VAC", -1, 8)
        cls._create_lot(cls.product_vaccine, "LOT-ZERO", 3, 0)

    @classmethod
    def _create_lot(cls, product, name, day_offset, qty):
        lot = cls.env["stock.lot"].create({
            "name": name,
            "product_id": product.id,
            "company_id": cls.env.company.id,
            "expiration_date": fields.Datetime.to_string(
                datetime.combine(fields.Date.today() + timedelta(days=day_offset), time.min)
            ),
        })
        if qty:
            cls.env["stock.quant"]._update_available_quantity(
                product, cls.stock_location, qty, lot_id=lot
            )
        return lot

    def test_get_product_expiry_returns_bucketed_quantities(self):
        dashboard = self.env["stock.lot"]

        result = dashboard.get_product_expiry({})

        self.assertDictEqual(result, {
            "expired": 15,
            "today": 2,
            "one_day": 3,
            "seven_day": 4,
            "thirty_day": 5,
            "one_twenty_day": 6,
        })

        filtered = dashboard.get_product_expiry({
            "start_date": fields.Date.today(),
            "end_date": fields.Date.today() + timedelta(days=7),
        })

        self.assertDictEqual(filtered, {
            "expired": 0,
            "today": 2,
            "one_day": 3,
            "seven_day": 4,
            "thirty_day": 0,
            "one_twenty_day": 0,
        })

    def test_get_expired_product_and_category_aggregate_quantities(self):
        dashboard = self.env["stock.lot"]

        expired_products = dashboard.get_expired_product({})
        self.assertDictEqual(expired_products, {
            "Expiry Yogurt": 7,
            "Expiry Vaccine": 8,
        })

        expired_categories = dashboard.get_product_expiry_by_category({})
        self.assertDictEqual(expired_categories, {
            "Expiry Test Food": 7,
            "Expiry Test Medicine": 8,
        })

    def test_get_near_expiry_methods_and_expired_today(self):
        dashboard = self.env["stock.lot"]

        near_products = dashboard.get_near_expiry_product()
        self.assertDictEqual(near_products, {
            "Expiry Yogurt": 3,
            "Expiry Juice": 4,
        })

        near_categories = dashboard.get_near_expiry_category()
        self.assertDictEqual(near_categories, {
            "Expiry Test Food": 7,
        })

        self.assertEqual(dashboard.get_product_expired_today(), 1)
