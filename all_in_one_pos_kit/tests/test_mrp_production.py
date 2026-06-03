# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestMrpProductionFromPos(TransactionCase):

    def test_create_mrp_from_pos_without_products_returns_true(self):
        self.assertTrue(self.env["mrp.production"].create_mrp_from_pos([]))
