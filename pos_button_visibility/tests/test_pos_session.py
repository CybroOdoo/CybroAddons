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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosSession(TransactionCase):
    """Test cases for pos.session data model loading."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({'name': 'Test Session Store'})

    def test_pos_session_load_pos_data_models_contains_pos_button(self):
        """Test that pos.session _load_pos_data_models includes 'pos.button'."""
        data_models = self.env['pos.session']._load_pos_data_models(self.pos_config)
        self.assertIn(
            'pos.button',
            data_models,
            "'pos.button' must be included in pos.session _load_pos_data_models."
        )

    def test_pos_session_load_pos_data_models_order(self):
        """Test that 'pos.button' is placed at index 0 in _load_pos_data_models."""
        data_models = self.env['pos.session']._load_pos_data_models(self.pos_config)
        self.assertEqual(
            data_models[0],
            'pos.button',
            "'pos.button' should be prepended at index 0 of the model loading list."
        )

    def test_pos_session_load_pos_data_models_no_duplicates(self):
        """Test that calling _load_pos_data_models does not introduce duplicate 'pos.button' entries."""
        data_models = self.env['pos.session']._load_pos_data_models(self.pos_config)
        self.assertEqual(
            data_models.count('pos.button'),
            1,
            "'pos.button' should only appear once in _load_pos_data_models."
        )
