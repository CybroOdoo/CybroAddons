# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestResConfigSettings(TransactionCase):

    def test_onchange_is_auto_generate_updates_company_flag(self):
        settings = self.env["res.config.settings"].new({
            "is_auto_generate": True,
        })
        self.env.company.check_auto_generate = False

        settings._onchange_is_auto_generate()

        self.assertTrue(self.env.company.check_auto_generate)

    def test_onchange_is_auto_generate_clears_company_flag(self):
        settings = self.env["res.config.settings"].new({
            "is_auto_generate": False,
        })
        self.env.company.check_auto_generate = True

        settings._onchange_is_auto_generate()

        self.assertFalse(self.env.company.check_auto_generate)
