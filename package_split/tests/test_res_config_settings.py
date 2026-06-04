# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestResConfigSettings(TransactionCase):

    def test_enable_package_split_matches_package_tracking_group(self):
        settings = self.env['res.config.settings'].create({
            'group_stock_tracking_lot': True,
        })

        self.assertTrue(settings.enable_package_split)

        settings.group_stock_tracking_lot = False
        self.assertFalse(settings.enable_package_split)
