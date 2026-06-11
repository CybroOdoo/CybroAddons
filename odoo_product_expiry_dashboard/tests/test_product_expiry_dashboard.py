# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import timedelta

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestProductExpiryDashboard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.today = fields.Date.today()
        
        # Clear existing expiration dates to prevent demo data from breaking test counts
        cls.env["stock.lot"].search([]).write({"expiration_date": False})

        cls.category_food = cls.env["product.category"].create({
            "name": "Expiry Food",
        })
        cls.category_drink = cls.env["product.category"].create({
            "name": "Expiry Drink",
        })
        cls.product_yogurt = cls.env["product.product"].create({
            "name": "Yogurt",
            "type": "consu",
            "is_storable": True,
            "categ_id": cls.category_food.id,
            "uom_id": cls.uom_unit.id,
            "uom_po_id": cls.uom_unit.id,
        })
        cls.product_milk = cls.env["product.product"].create({
            "name": "Milk",
            "type": "consu",
            "is_storable": True,
            "categ_id": cls.category_drink.id,
            "uom_id": cls.uom_unit.id,
            "uom_po_id": cls.uom_unit.id,
        })

        cls.expired_lot = cls._create_lot_with_quant(
            cls.product_yogurt, cls.today - timedelta(days=1), 2.0
        )
        cls.today_lot = cls._create_lot_with_quant(
            cls.product_yogurt, cls.today, 3.0
        )
        cls.one_day_lot = cls._create_lot_with_quant(
            cls.product_milk, cls.today + timedelta(days=1), 4.0
        )
        cls.seven_day_lot = cls._create_lot_with_quant(
            cls.product_milk, cls.today + timedelta(days=5), 5.0
        )
        cls.thirty_day_lot = cls._create_lot_with_quant(
            cls.product_yogurt, cls.today + timedelta(days=15), 6.0
        )
        cls.one_twenty_day_lot = cls._create_lot_with_quant(
            cls.product_milk, cls.today + timedelta(days=60), 7.0
        )
        cls.zero_qty_lot = cls._create_lot_with_quant(
            cls.product_yogurt, cls.today + timedelta(days=2), 0.0
        )

    @classmethod
    def _create_lot_with_quant(cls, product, expiration_date, quantity):
        lot = cls.env["stock.lot"].create({
            "name": f"{product.name}-{expiration_date}",
            "product_id": product.id,
            "expiration_date": fields.Date.to_string(expiration_date),
            "company_id": cls.env.company.id,
        })
        cls.env["stock.quant"].create({
            "product_id": product.id,
            "location_id": cls.stock_location.id,
            "lot_id": lot.id,
            "quantity": quantity,
        })
        return lot

    def test_get_product_expiry_bucket_totals(self):
        result = self.env["stock.lot"].get_product_expiry({})

        self.assertEqual(result, {
            "expired": 2.0,
            "today": 3.0,
            "one_day": 4.0,
            "seven_day": 9.0,
            "thirty_day": 15.0,
            "one_twenty_day": 22.0,
        })

    def test_get_product_expiry_respects_date_filters(self):
        result = self.env["stock.lot"].get_product_expiry({
            "start_date": fields.Date.to_string(self.today),
            "end_date": fields.Date.to_string(self.today + timedelta(days=7)),
        })

        self.assertEqual(result, {
            "expired": 0,
            "today": 3.0,
            "one_day": 4.0,
            "seven_day": 9.0,
            "thirty_day": 9.0,
            "one_twenty_day": 9.0,
        })

    def test_expired_product_and_category_aggregation(self):
        expired_products = self.env["stock.lot"].get_expired_product({})
        expired_categories = self.env["stock.lot"].get_product_expiry_by_category({})

        self.assertEqual(expired_products, {"Yogurt": 2.0})
        self.assertEqual(expired_categories, {"Expiry Food": 2.0})

    def test_near_expiry_product_and_category_aggregation(self):
        nearby_products = self.env["stock.lot"].get_near_expiry_product()
        nearby_categories = self.env["stock.lot"].get_near_expiry_category()

        self.assertEqual(nearby_products, {
            "Milk": 9.0,
        })
        self.assertEqual(nearby_categories, {
            "Expiry Drink": 9.0,
        })

    def test_get_product_expired_today_counts_lots(self):
        result = self.env["stock.lot"].get_product_expired_today()

        self.assertEqual(result, 1)
