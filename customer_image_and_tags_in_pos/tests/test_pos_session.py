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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Test suite for pos.session model extension."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosSession(TransactionCase):
    """Test suite covering POS session data model loading."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].search([], limit=1)
        if not cls.pos_config:
            cls.pos_config = cls.env['pos.config'].create({'name': 'Test POS Config'})

    def test_load_pos_data_models_contains_partner_category(self):
        """Test that pos.session._load_pos_data_models includes 'res.partner.category'."""
        loaded_models = self.env['pos.session']._load_pos_data_models(self.pos_config)
        self.assertIn(
            'res.partner.category',
            loaded_models,
            "res.partner.category must be included in the POS data models to load."
        )

    def test_load_pos_data_models_preserves_base_models(self):
        """Test that default core models are preserved when extending _load_pos_data_models."""
        loaded_models = self.env['pos.session']._load_pos_data_models(self.pos_config)
        self.assertIn('pos.config', loaded_models)
        self.assertIn('res.partner', loaded_models)
        self.assertIn('product.product', loaded_models)
