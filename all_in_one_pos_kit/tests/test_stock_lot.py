# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestStockLot(TransactionCase):

    def test_get_available_lots_for_pos_without_stock_returns_empty_list(self):
        product = self.env["product.product"].create({
            "name": "Lot Tracked POS Product",
            "tracking": "lot",
        })

        self.assertEqual(
            self.env["stock.lot"].get_available_lots_for_pos(product.id),
            [],
        )
