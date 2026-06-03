# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestResConfigSettings(TransactionCase):

    def test_set_and_get_values_store_sms_body(self):
        settings = self.env["res.config.settings"].create({
            "sms_body": "Thank you for shopping",
        })

        settings.set_values()
        values = settings.get_values()

        self.assertEqual(
            self.env["ir.config_parameter"].sudo().get_param("pos.sms_body"),
            "Thank you for shopping",
        )
        self.assertEqual(values["sms_body"], "Thank you for shopping")
