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
import os
import odoo.modules.module as module_utils
from odoo.tests.common import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosNumpadShowHide(TransactionCase):
    """Test suite for POS Numpad Show/Hide module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test Numpad POS Config',
        })

    def test_01_pos_numpad_module_installed(self):
        """Verify that pos_numpad_show_hide is installed and valid."""
        module = self.env['ir.module.module'].search([('name', '=', 'pos_numpad_show_hide')], limit=1)
        self.assertTrue(module)
        self.assertEqual(module.state, 'installed')

    def test_02_pos_session_initialization(self):
        """Verify POS session can be initialized cleanly with pos_numpad_show_hide active."""
        session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
            'user_id': self.env.uid,
        })
        self.assertTrue(session)
        self.assertEqual(session.state, 'opening_control')

    def test_03_assets_bundle_inclusion(self):
        """Verify static files are present in the module tree."""
        mod_path = module_utils.get_module_path('pos_numpad_show_hide')
        self.assertTrue(mod_path)
        self.assertTrue(os.path.exists(os.path.join(mod_path, 'static/src/xml/pos.xml')))
        self.assertTrue(os.path.exists(os.path.join(mod_path, 'static/src/js/pos_numpad.js')))


@tagged('post_install', '-at_install')
class TestPosNumpadTour(HttpCase):
    """Tour tests for POS Numpad Show/Hide UI toggle."""

    def test_pos_numpad_show_hide_tour(self):
        """Start POS tour and verify numpad toggle button and eye icon."""
        pos_config = self.env['pos.config'].create({'name': 'Tour Numpad POS Config'})
        self.start_tour(f"/pos/ui/{pos_config.id}", 'pos_numpad_show_hide_tour', login='admin')
