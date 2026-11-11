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
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', 'at_install')
class TestResPartner(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config_param = cls.env['ir.config_parameter'].sudo()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner Inc',
            'street': '123 Main St',
            'street2': 'Suite 100',
            'city': 'San Francisco',
            'zip': '94105',
        })

    def _set_config(self, key, value):
        params = self.config_param
        if hasattr(params, 'set_str'):
            params.set_str(key, value)
        elif hasattr(params, 'set_param'):
            params.set_param(key, value)

    def test_is_address_extraction_enabled_default_and_toggle(self):
        """Test checking if address autofill is enabled in settings."""
        self._set_config('ai_address_autofill.address_autofill', 'True')
        self.assertTrue(self.partner._is_address_extraction_enabled())

        self._set_config('ai_address_autofill.address_autofill', 'False')
        self.assertFalse(self.partner._is_address_extraction_enabled())

    def test_is_address_extraction_enabled_legacy_fallback(self):
        """Test fallback to legacy configuration keys when primary key is absent."""
        rec = self.config_param.search([('key', '=', 'ai_address_autofill.address_autofill')])
        if rec:
            rec.unlink()

        self._set_config('ai_address_autofill.enable_address_extraction', 'True')
        self.assertTrue(self.partner._is_address_extraction_enabled())

    def test_compute_show_address_autofill_button(self):
        """Test computed button visibility matches setting."""
        self._set_config('ai_address_autofill.address_autofill', 'True')
        self.partner._compute_show_address_autofill_button()
        self.assertTrue(self.partner.show_address_autofill_button)

        self._set_config('ai_address_autofill.address_autofill', 'False')
        self.partner._compute_show_address_autofill_button()
        self.assertFalse(self.partner.show_address_autofill_button)

    def test_check_address_extraction_list_enabled(self):
        """Test model method used by OWL Cog menu."""
        self._set_config('ai_address_autofill.address_autofill', 'True')
        self.assertTrue(self.env['res.partner'].check_address_extraction_list_enabled())

    def test_action_open_address_extractor_enabled(self):
        """Test opening wizard returns correct act_window with partner context."""
        self._set_config('ai_address_autofill.address_autofill', 'True')
        action = self.partner.action_open_address_extractor()

        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'address.extraction.wizard')
        self.assertEqual(action.get('target'), 'new')
        ctx = action.get('context', {})
        self.assertEqual(ctx.get('default_partner_id'), self.partner.id)
        self.assertTrue(ctx.get('default_is_partner_readonly'))
        self.assertIn("123 Main St", ctx.get('default_raw_address', ''))

    def test_action_open_address_extractor_disabled_raises_user_error(self):
        """Test opening wizard raises UserError when extraction is disabled."""
        self._set_config('ai_address_autofill.address_autofill', 'False')
        with self.assertRaises(UserError):
            self.partner.action_open_address_extractor()
