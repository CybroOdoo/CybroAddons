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
"""Unit tests for res.config.settings stock transfer configuration."""
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettingsStockTransfer(TransactionCase):
    """Test stock transfer configuration on res.config.settings."""

    def setUp(self):
        super().setUp()
        self.pos_config = self.env['pos.config'].create({
            'name': 'Settings Stock Transfer POS',
            'stock_transfer': False,
        })

    def test_settings_toggle_enable(self):
        """Test enabling stock transfer via res.config.settings."""
        settings = self.env['res.config.settings'].with_context(
            pos_config_id=self.pos_config.id
        ).create({
            'pos_config_id': self.pos_config.id,
            'is_stock_transfer': True,
        })
        # Verify related write behavior
        self.assertTrue(settings.is_stock_transfer)
        self.assertTrue(self.pos_config.stock_transfer)

    def test_settings_toggle_disable(self):
        """Test disabling stock transfer via res.config.settings."""
        self.pos_config.stock_transfer = True
        settings = self.env['res.config.settings'].with_context(
            pos_config_id=self.pos_config.id
        ).create({
            'pos_config_id': self.pos_config.id,
            'is_stock_transfer': False,
        })
        self.assertFalse(settings.is_stock_transfer)
        self.assertFalse(self.pos_config.stock_transfer)

    def test_settings_read(self):
        """Test reading the stock transfer value from settings."""
        self.pos_config.stock_transfer = True
        settings = self.env['res.config.settings'].with_context(
            pos_config_id=self.pos_config.id
        ).new({'pos_config_id': self.pos_config.id})
        self.assertTrue(settings.is_stock_transfer)
