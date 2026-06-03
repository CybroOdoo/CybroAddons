# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestPosSession(TransactionCase):

    def test_load_pos_data_models_includes_custom_models(self):
        models = self.env["pos.session"]._load_pos_data_models(False)

        self.assertIn("multi.barcode.products", models)
        self.assertIn("meals.planning", models)
