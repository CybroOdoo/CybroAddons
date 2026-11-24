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
from odoo.tests import TransactionCase, new_test_user, tagged

from odoo.addons.minimal_backend_theme.models.global_search import (
    DEFAULT_SEARCH_MODELS,
    SEARCH_MODELS_PARAM,
)


@tagged('post_install', '-at_install')
class TestGlobalSearch(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ICP = cls.env['ir.config_parameter'].sudo()
        cls.ICP.search([('key', '=', SEARCH_MODELS_PARAM)]).unlink()
        cls.Search = cls.env['minimal_backend_theme.global_search']
        cls.partners = cls.env['res.partner'].create([
            {'name': f'Quokka Trading {i}'} for i in range(7)
        ])

    def test_defaults_skip_models_not_installed(self):
        names = self.Search._get_search_model_names()
        self.assertIn('res.partner', names)
        for name in DEFAULT_SEARCH_MODELS:
            self.assertEqual(name in names, name in self.env, name)

    def test_results_grouped_by_model_with_limit(self):
        groups = self.Search.search_records('quokka trad')
        partner_group = next(g for g in groups if g['model'] == 'res.partner')
        self.assertEqual(len(partner_group['records']), 5)
        self.assertTrue(partner_group['has_more'])
        self.assertTrue(partner_group['label'])
        self.assertTrue(all('Quokka Trading' in r['display_name'] for r in partner_group['records']))
        # Points to a menu opening contacts when an app has one (Contacts,
        # CRM...), to open them in their app; none in a bare database.
        partner_menus = self.env['ir.ui.menu'].search([])._filter_visible_menus().filtered(
            lambda menu: menu.action and menu.action._name == 'ir.actions.act_window'
            and menu.action.res_model == 'res.partner',
        )
        if partner_menus:
            menu = self.env['ir.ui.menu'].browse(partner_group['menu_id'])
            self.assertIn(menu, partner_menus)
        else:
            self.assertFalse(partner_group['menu_id'])

    def test_short_or_empty_query(self):
        self.assertEqual(self.Search.search_records('q'), [])
        self.assertEqual(self.Search.search_records('  '), [])
        self.assertEqual(self.Search.search_records('no-such-record-xyz'), [])

    def test_settings_choice_and_none(self):
        self.ICP.set_str(SEARCH_MODELS_PARAM, 'res.country,not.a.model, res.partner')
        self.assertEqual(self.Search._get_search_model_names(), ['res.country', 'res.partner'])
        groups = self.Search.search_records('belgi')
        self.assertEqual([g['model'] for g in groups], ['res.country'])

        self.ICP.set_str(SEARCH_MODELS_PARAM, '')
        self.assertEqual(self.Search._get_search_model_names(), [])
        self.assertEqual(self.Search.search_records('quokka'), [])

    def test_settings_form_round_trip(self):
        settings = self.env['res.config.settings'].create({})
        self.assertIn('res.partner', settings.minimal_theme_search_model_ids.mapped('model'))
        country_model = self.env['ir.model']._get('res.country')
        settings.minimal_theme_search_model_ids = country_model
        settings.execute()
        self.assertEqual(self.ICP.get_str(SEARCH_MODELS_PARAM), 'res.country')

    def test_models_without_access_are_skipped(self):
        # Only administrators can read system parameters.
        self.ICP.set_str(SEARCH_MODELS_PARAM, 'ir.config_parameter,res.partner')
        user = new_test_user(self.env, login='global_search_user', groups='base.group_user')
        groups = self.Search.with_user(user).search_records('minimal_backend_theme')
        self.assertNotIn('ir.config_parameter', [g['model'] for g in groups])
        admin_groups = self.Search.search_records('minimal_backend_theme')
        self.assertIn('ir.config_parameter', [g['model'] for g in admin_groups])
