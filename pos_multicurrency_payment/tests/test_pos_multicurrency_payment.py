# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################

from odoo.tests.common import TransactionCase


class TestPosMultiCurrency(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company

        cls.currency = cls.env.ref("base.USD")

        cls.pos_config = cls.env["pos.config"].create({
            "name": "Test POS",
            "company_id": cls.company.id,
            "pos_multi_currency_enabled": True,
            "pos_multi_currency_conversion": True,
            "pos_allowed_currency_ids": [(6, 0, [cls.currency.id])],
        })

    # ------------------------------------------------------------------
    # POS Configuration
    # ------------------------------------------------------------------

    def test_configuration_fields(self):
        self.assertTrue(self.pos_config.pos_multi_currency_enabled)
        self.assertTrue(self.pos_config.pos_multi_currency_conversion)
        self.assertEqual(
            self.pos_config.pos_allowed_currency_ids,
            self.currency
        )

    # ------------------------------------------------------------------
    # Allowed Currency Data
    # ------------------------------------------------------------------

    def test_get_limited_currencies_data(self):
        data = self.pos_config.get_limited_currencies_data()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.currency.id)
        self.assertEqual(data[0]["name"], self.currency.name)
        self.assertEqual(data[0]["symbol"], self.currency.symbol)

    # ------------------------------------------------------------------
    # Session Info
    # ------------------------------------------------------------------

    def test_get_pos_session_info(self):
        result = self.pos_config.get_pos_session_info()

        self.assertTrue(result["pos_multi_currency_enabled"])
        self.assertTrue(result["pos_multi_currency_conversion"])
        self.assertEqual(len(result["pos_allowed_currencies"]), 1)

    # ------------------------------------------------------------------
    # Disabled Configuration
    # ------------------------------------------------------------------

    def test_disabled_configuration(self):
        self.pos_config.write({
            "pos_multi_currency_enabled": False,
        })

        result = self.pos_config.get_pos_session_info()

        self.assertFalse(result["pos_multi_currency_enabled"])
        self.assertFalse(result["pos_multi_currency_conversion"])
        self.assertEqual(result["pos_allowed_currencies"], [])

    # ------------------------------------------------------------------
    # Inject Currency Data
    # ------------------------------------------------------------------

    def test_inject_multi_currency_data(self):

        session = self.env["pos.session"].new({
            "config_id": self.pos_config.id,
        })

        loaded_data = {
            "pos.config": [{
                "id": self.pos_config.id,
            }]
        }

        session._inject_multi_currency_data(loaded_data)

        config = loaded_data["pos.config"][0]

        self.assertTrue(config["pos_multi_currency_enabled"])
        self.assertTrue(config["pos_multi_currency_conversion"])
        self.assertEqual(
            config["pos_allowed_currency_ids"],
            [self.currency.id],
        )
        self.assertEqual(
            len(config["pos_allowed_currencies_data"]),
            1,
        )