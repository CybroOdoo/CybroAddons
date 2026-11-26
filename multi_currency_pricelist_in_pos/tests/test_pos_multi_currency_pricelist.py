# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#############################################################################
from odoo import Command
from odoo.addons.point_of_sale.tests.common import TestPoSCommon
from odoo.exceptions import ValidationError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestPosMultiCurrencyPricelist(TestPoSCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.other_currency_pricelist = cls.env["product.pricelist"].create({
            "name": "Multi Currency Pricelist",
            "currency_id": cls.other_currency.id,
        })

    def test_rejects_mixed_currency_pricelists_when_feature_disabled(self):
        with self.assertRaises(ValidationError):
            self.basic_config.write({
                "use_pricelist": True,
                "enable_multi_currency_pricelist": False,
                "available_pricelist_ids": [
                    Command.set(
                        (
                            self.basic_config.pricelist_id
                            | self.other_currency_pricelist
                        ).ids
                    )
                ],
            })

    def test_allows_mixed_currency_pricelists_when_feature_enabled(self):
        mixed_pricelists = self.basic_config.pricelist_id | self.other_currency_pricelist

        self.basic_config.write({
            "use_pricelist": True,
            "enable_multi_currency_pricelist": True,
            "available_pricelist_ids": [Command.set(mixed_pricelists.ids)],
        })

        self.assertEqual(
            set(self.basic_config.available_pricelist_ids.ids),
            set(mixed_pricelists.ids),
        )

    def test_requires_default_pricelist_to_stay_available(self):
        with self.assertRaises(ValidationError):
            self.basic_config.write({
                "use_pricelist": True,
                "enable_multi_currency_pricelist": True,
                "pricelist_id": self.basic_config.pricelist_id.id,
                "available_pricelist_ids": [Command.set(self.other_currency_pricelist.ids)],
            })

    def test_settings_keep_existing_pricelists_when_feature_enabled(self):
        mixed_pricelists = self.basic_config.pricelist_id | self.other_currency_pricelist
        self.basic_config.write({
            "use_pricelist": True,
            "enable_multi_currency_pricelist": True,
            "available_pricelist_ids": [Command.set(mixed_pricelists.ids)],
        })

        settings = self.env["res.config.settings"].new({
            "pos_config_id": self.basic_config.id,
            "pos_use_pricelist": True,
            "pos_enable_multi_currency_pricelist": True,
            "pos_available_pricelist_ids": [Command.set(mixed_pricelists.ids)],
        })
        settings._compute_pos_pricelist_id()

        self.assertEqual(
            set(settings.pos_available_pricelist_ids.ids),
            set(mixed_pricelists.ids),
        )
        self.assertEqual(settings.pos_pricelist_id, self.basic_config.pricelist_id)

    def test_settings_filter_pricelists_to_config_currency_when_feature_disabled(self):
        mixed_pricelists = self.basic_config.pricelist_id | self.other_currency_pricelist
        self.basic_config.write({
            "use_pricelist": True,
            "enable_multi_currency_pricelist": True,
            "available_pricelist_ids": [Command.set(mixed_pricelists.ids)],
        })

        settings = self.env["res.config.settings"].new({
            "pos_config_id": self.basic_config.id,
            "pos_use_pricelist": True,
            "pos_enable_multi_currency_pricelist": False,
            "pos_available_pricelist_ids": [Command.set(mixed_pricelists.ids)],
        })
        settings._compute_pos_pricelist_id()

        self.assertNotIn(self.other_currency_pricelist, settings.pos_available_pricelist_ids)
        self.assertTrue(settings.pos_available_pricelist_ids)
        self.assertTrue(
            all(
                pricelist.currency_id == self.basic_config.currency_id
                for pricelist in settings.pos_available_pricelist_ids
            )
        )
        self.assertEqual(settings.pos_pricelist_id.currency_id, self.basic_config.currency_id)

    def test_loader_params_include_pricelist_currency_field_once(self):
        self.config = self.basic_config
        pos_session = self.open_new_session()

        fields = pos_session._loader_params_product_pricelist()["search_params"]["fields"]

        self.assertIn("currency_id", fields)
        self.assertEqual(fields.count("currency_id"), 1)

    def test_load_pos_data_exposes_multi_currency_payload_only_when_enabled(self):
        # Feature disabled: only same-currency pricelists are allowed, so the
        # config must not contain mixed-currency pricelists here.
        self.basic_config.write({
            "use_pricelist": True,
            "enable_multi_currency_pricelist": False,
            "available_pricelist_ids": [
                Command.set(self.basic_config.pricelist_id.ids)
            ],
        })

        self.config = self.basic_config
        disabled_session = self.open_new_session()
        disabled_data = disabled_session.load_pos_data()

        self.assertEqual(disabled_data["multi_currency_pricelist_currencies"], [])

        enabled_pricelists = self.other_currency_config.pricelist_id | self.basic_config.pricelist_id
        self.other_currency_config.write({
            "use_pricelist": True,
            "enable_multi_currency_pricelist": True,
            "available_pricelist_ids": [Command.set(enabled_pricelists.ids)],
        })

        self.config = self.other_currency_config
        enabled_session = self.open_new_session()
        enabled_data = enabled_session.load_pos_data()
        currency_rows = enabled_data["multi_currency_pricelist_currencies"]
        returned_currency_ids = {currency["id"] for currency in currency_rows}

        self.assertIn(self.other_currency_config.currency_id.id, returned_currency_ids)
        self.assertIn(self.other_currency.id, returned_currency_ids)
        self.assertIn(self.company.currency_id.id, returned_currency_ids)
        self.assertTrue(
            all(
                {"name", "symbol", "position", "rounding", "rate", "decimal_places"} <= currency.keys()
                for currency in currency_rows
            )
        )

    def test_rejects_payment_method_in_other_currency(self):
        with self.assertRaises(ValidationError):
            self.basic_config.write({
                "payment_method_ids": [Command.link(self.cash_pm2.id)],
            })

    def test_rejects_invoice_journal_in_other_currency(self):
        with self.assertRaises(ValidationError):
            self.basic_config.write({
                "invoice_journal_id": self.other_currency_config.invoice_journal_id.id,
            })

    def test_settings_clear_pricelist_when_pricelists_disabled(self):
        settings = self.env["res.config.settings"].new({
            "pos_config_id": self.basic_config.id,
            "pos_use_pricelist": False,
        })
        settings._compute_pos_pricelist_id()

        self.assertFalse(settings.pos_pricelist_id)

    def test_settings_keep_pricelists_when_all_in_config_currency(self):
        settings = self.env["res.config.settings"].new({
            "pos_config_id": self.basic_config.id,
            "pos_use_pricelist": True,
            "pos_enable_multi_currency_pricelist": False,
            "pos_available_pricelist_ids": [
                Command.set(self.basic_config.pricelist_id.ids)
            ],
        })
        settings._compute_pos_pricelist_id()

        self.assertEqual(
            set(settings.pos_available_pricelist_ids.ids),
            set(self.basic_config.available_pricelist_ids.ids),
        )
        self.assertEqual(
            settings.pos_pricelist_id.id, self.basic_config.pricelist_id.id
        )
