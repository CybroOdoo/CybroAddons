# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo import Command
from odoo.addons.point_of_sale.tests.common import TestPoSCommon
from odoo.exceptions import ValidationError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestPosMultiCurrencyPricelist(TestPoSCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.other_pricelist = cls.other_currency_config.pricelist_id
        cls.mixed_currency_config = cls.env["pos.config"].create({
            "name": "Mixed Currency POS",
            "journal_id": cls.basic_config.journal_id.id,
            "invoice_journal_id": cls.basic_config.invoice_journal_id.id,
            "use_pricelist": True,
            "available_pricelist_ids": [Command.set([
                cls.currency_pricelist.id,
                cls.other_pricelist.id,
            ])],
            "pricelist_id": cls.currency_pricelist.id,
            "enable_multi_currency_pricelist": True,
        })
        cls.product = cls.create_product(
            "POS Multi Currency Product",
            cls.categ_basic,
            100.0,
            50.0,
        )
        cls.vendor = cls.env["res.partner"].create({
            "name": "POS Multi Currency Vendor",
            "supplier_rank": 1,
        })
        cls.supplierinfo = cls.env["product.supplierinfo"].create({
            "partner_id": cls.vendor.id,
            "product_tmpl_id": cls.product.product_tmpl_id.id,
            "min_qty": 1.0,
            "price": 42.0,
            "delay": 3,
            "currency_id": cls.other_currency.id,
        })

    def test_mixed_currency_pricelists_are_blocked_when_disabled(self):
        with self.assertRaises(ValidationError):
            self.env["pos.config"].create({
                "name": "Blocked Mixed Currency POS",
                "journal_id": self.basic_config.journal_id.id,
                "invoice_journal_id": self.basic_config.invoice_journal_id.id,
                "use_pricelist": True,
                "available_pricelist_ids": [Command.set([
                    self.currency_pricelist.id,
                    self.other_pricelist.id,
                ])],
                "pricelist_id": self.currency_pricelist.id,
            })

    def test_mixed_currency_pricelists_are_allowed_when_enabled(self):
        self.assertTrue(self.mixed_currency_config.enable_multi_currency_pricelist)
        self.assertEqual(
            self.mixed_currency_config.available_pricelist_ids,
            self.currency_pricelist | self.other_pricelist,
        )

    def test_pos_pricelist_fields_include_currency_id(self):
        loaded_fields = self.env["product.pricelist"]._load_pos_data_fields(
            self.mixed_currency_config.id
        )

        self.assertIn("currency_id", loaded_fields)

    def test_currency_domain_uses_only_pos_related_currencies(self):
        data = {
            "pos.config": {
                "data": [{
                    "id": self.mixed_currency_config.id,
                    "company_id": self.mixed_currency_config.company_id.id,
                    "currency_id": self.mixed_currency_config.currency_id.id,
                }],
            },
        }

        domain = self.env["res.currency"]._load_pos_data_domain(data)

        self.assertEqual(domain[0][0], "id")
        self.assertEqual(domain[0][1], "in")
        self.assertEqual(
            set(domain[0][2]),
            {
                self.company_currency.id,
                self.other_currency.id,
            },
        )

    def test_settings_keep_mixed_currency_pricelists_when_feature_enabled(self):
        settings = self.env["res.config.settings"].create({
            "pos_config_id": self.mixed_currency_config.id,
        })
        settings._compute_pos_pricelist_id()

        self.assertEqual(
            settings.pos_available_pricelist_ids,
            self.mixed_currency_config.available_pricelist_ids,
        )
        self.assertEqual(settings.pos_pricelist_id, self.mixed_currency_config.pricelist_id)

    def test_get_product_info_pos_adds_currency_to_pricelists_and_suppliers(self):
        info = self.product.get_product_info_pos(
            self.product.lst_price,
            1,
            self.mixed_currency_config.id,
        )

        self.assertIn("all_prices", info)
        self.assertIn("warehouses", info)
        self.assertIn("variants", info)
        self.assertEqual(
            {
                pricelist_info["id"]: pricelist_info["currency_id"]
                for pricelist_info in info["pricelists"]
            },
            {
                self.currency_pricelist.id: self.company_currency.id,
                self.other_pricelist.id: self.other_currency.id,
            },
        )
        self.assertEqual(len(info["suppliers"]), 1)
        self.assertEqual(
            info["suppliers"][0],
            {
                "id": self.supplierinfo.id,
                "name": self.vendor.name,
                "delay": self.supplierinfo.delay,
                "price": self.supplierinfo.price,
                "currency_id": self.other_currency.id,
            },
        )
