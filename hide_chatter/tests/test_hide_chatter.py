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
from odoo.tests.common import TransactionCase, new_test_user


class TestHideChatter(TransactionCase):
    """Check that the hide-chatter configuration round-trips and is readable
    by non-administrator users."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['ir.model']._get('res.partner')
        self.param = self.env['ir.config_parameter']

    def _save_hidden_models(self, models):
        """Store the given 'ir.model' recordset through the settings flow."""
        settings = self.env['res.config.settings'].create({
            'model_ids': [(6, 0, models.ids)],
        })
        settings.set_values()

    def test_set_values_stores_string_parameter(self):
        """set_values stores the ids as a string parameter."""
        self._save_hidden_models(self.partner_model)
        self.assertEqual(
            self.param.get_str('hide_chatter.model_ids'),
            str(self.partner_model.ids),
            "The selected model ids should be stored as a string.")

    def test_get_values_round_trip(self):
        """get_values reads back exactly the stored models."""
        self._save_hidden_models(self.partner_model)
        values = self.env['res.config.settings'].get_values()
        self.assertEqual(
            values['model_ids'], [(6, 0, self.partner_model.ids)],
            "get_values should return the models saved by set_values.")

    def test_hidden_models_returns_technical_names(self):
        """get_hidden_chatter_models returns the technical model names."""
        self._save_hidden_models(self.partner_model)
        self.assertEqual(
            self.env['ir.model'].get_hidden_chatter_models(),
            ['res.partner'],
            "The helper should return the technical name of hidden models.")

    def test_hidden_models_readable_by_non_admin(self):
        """A standard internal user can read the hidden models even though the
        underlying system parameter is admin-only."""
        self._save_hidden_models(self.partner_model)
        user = new_test_user(self.env, login='hide_chatter_user')
        hidden = self.env['ir.model'].with_user(user).get_hidden_chatter_models()
        self.assertEqual(
            hidden, ['res.partner'],
            "Non-admin users must receive the hidden models list.")

    def test_no_configuration_returns_empty_list(self):
        """Without any stored configuration the helper returns an empty list."""
        self.param.set_str('hide_chatter.model_ids', '')
        self.assertEqual(
            self.env['ir.model'].get_hidden_chatter_models(), [],
            "An empty configuration should yield no hidden models.")
