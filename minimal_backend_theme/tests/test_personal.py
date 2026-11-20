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


@tagged('post_install', '-at_install')
class TestPinnedMenus(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Pin = cls.env['minimal_backend_theme.menu_pin']
        cls.user_a = new_test_user(cls.env, login='pin_user_a', groups='base.group_user')
        cls.user_b = new_test_user(cls.env, login='pin_user_b', groups='base.group_user')
        Menu = cls.env['ir.ui.menu']
        # Menus need an action to be shown at all.
        action = cls.env['ir.actions.act_window'].create({
            'name': 'Pin Test', 'res_model': 'res.partner', 'view_mode': 'list,form',
        })
        # A menu every internal user sees, and one only administrators see.
        cls.public_menu = Menu.create({'name': 'Pin Test Public', 'action': f'ir.actions.act_window,{action.id}'})
        cls.admin_menu = Menu.create({
            'name': 'Pin Test Admin Only',
            'action': f'ir.actions.act_window,{action.id}',
            'group_ids': [(6, 0, [cls.env.ref('base.group_system').id])],
        })

    def test_toggle_pins_and_unpins(self):
        Pin = self.Pin.with_user(self.user_a)
        self.assertEqual(Pin.toggle_pin(self.public_menu.id), [self.public_menu.id])
        self.assertEqual(Pin.get_pinned_menu_ids(), [self.public_menu.id])
        self.assertEqual(Pin.toggle_pin(self.public_menu.id), [])

    def test_pins_are_personal(self):
        self.Pin.with_user(self.user_a).toggle_pin(self.public_menu.id)
        self.assertEqual(self.Pin.with_user(self.user_b).get_pinned_menu_ids(), [])
        self.assertFalse(self.Pin.with_user(self.user_b).search([]))
        # User b toggling the same menu pins it for b, without touching a's pin.
        self.Pin.with_user(self.user_b).toggle_pin(self.public_menu.id)
        self.assertEqual(self.Pin.with_user(self.user_a).get_pinned_menu_ids(), [self.public_menu.id])

    def test_cannot_pin_a_menu_one_cannot_see(self):
        self.assertEqual(self.Pin.with_user(self.user_a).toggle_pin(self.admin_menu.id), [])
        self.assertFalse(self.Pin.sudo().search([('user_id', '=', self.user_a.id)]))

    def test_menus_no_longer_visible_are_dropped(self):
        self.Pin.with_user(self.user_a).toggle_pin(self.public_menu.id)
        self.public_menu.group_ids = self.env.ref('base.group_system')
        self.assertEqual(self.Pin.with_user(self.user_a).get_pinned_menu_ids(), [])

    def test_pinned_ids_reach_the_web_client(self):
        self.Pin.toggle_pin(self.public_menu.id)
        settings = self.env['res.config.settings']._minimal_theme_get_settings()
        self.assertNotIn('pinned_menu_ids', settings)  # personal: sent apart
        self.assertIn(self.public_menu.id, self.Pin.get_pinned_menu_ids())


@tagged('post_install', '-at_install')
class TestRecentRecordsAndCreate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Search = cls.env['minimal_backend_theme.global_search']
        cls.user = new_test_user(cls.env, login='recent_user', groups='base.group_user')
        cls.partners = cls.env['res.partner'].create([{'name': f'Recent Partner {i}'} for i in range(3)])

    def test_recent_records_are_checked(self):
        deleted = self.env['res.partner'].create({'name': 'Gone'})
        deleted_id = deleted.id
        deleted.unlink()
        param = self.env['ir.config_parameter'].sudo().search([], limit=1)
        entries = [
            {'model': 'res.partner', 'id': self.partners[0].id},
            {'model': 'res.partner', 'id': deleted_id},                 # deleted
            {'model': 'res.config.settings', 'id': 1},                  # transient
            {'model': 'no.such.model', 'id': 1},                        # unknown
            {'model': 'res.partner', 'id': 'x'},                        # malformed
            {'model': 'ir.config_parameter', 'id': param.id},           # admin only
            {'model': 'res.partner', 'id': self.partners[0].id},        # duplicate
            {'model': 'res.partner', 'id': self.partners[1].id},
        ]
        records = self.Search.with_user(self.user).get_recent_records(entries)
        self.assertEqual(
            [(r['model'], r['id']) for r in records],
            [('res.partner', self.partners[0].id), ('res.partner', self.partners[1].id)],
        )
        self.assertEqual(records[0]['display_name'], 'Recent Partner 0')
        self.assertTrue(records[0]['label'])
        # Administrators can read system parameters.
        admin_records = self.Search.get_recent_records(entries)
        self.assertIn(('ir.config_parameter', param.id), [(r['model'], r['id']) for r in admin_records])

    def test_recent_records_limit(self):
        entries = [{'model': 'res.partner', 'id': p.id} for p in self.partners]
        self.assertEqual(len(self.Search.get_recent_records(entries, limit=2)), 2)

    def test_create_targets_respect_create_rights(self):
        for user in (self.env.user, self.user):
            targets = self.Search.with_user(user).get_create_targets()
            self.assertTrue(targets)
            models_seen = [t['model'] for t in targets]
            self.assertEqual(len(models_seen), len(set(models_seen)), "one entry per record type")
            for target in targets:
                Model = self.env[target['model']].with_user(user)
                self.assertTrue(Model.has_access('create'), target['model'])
                menu = self.env['ir.ui.menu'].with_user(user).browse(target['menu_id'])
                self.assertTrue(menu._filter_visible_menus(), "opened through a menu the user can see")
                self.assertEqual(menu.action.res_model, target['model'])
                self.assertIn('form', menu.action.sudo().view_mode.split(','))
        # Contacts' main record type comes before configuration records.
        if self.env['ir.module.module']._get('contacts').state == 'installed':
            ordered = [t['model'] for t in self.Search.get_create_targets()]
            self.assertLess(ordered.index('res.partner'), ordered.index('res.country'))
        admin_models = {t['model'] for t in self.Search.get_create_targets()}
        user_models = {t['model'] for t in self.Search.with_user(self.user).get_create_targets()}
        self.assertLessEqual(user_models, admin_models)


@tagged('post_install', '-at_install')
class TestMenuChoice(TransactionCase):

    def test_records_open_in_the_app_with_most_menus_for_them(self):
        """An app with a single menu on a model (CRM's "My Quotations" for
        sales orders) loses to the app made for it (Sales), even if first."""
        Menu = self.env['ir.ui.menu']
        action = self.env['ir.actions.act_window'].create({
            'name': 'Choice', 'res_model': 'res.partner.category', 'view_mode': 'list,form',
        })
        ref = f'ir.actions.act_window,{action.id}'
        side_app = Menu.create({'name': 'Side App', 'sequence': 1})
        main_app = Menu.create({'name': 'Main App', 'sequence': 2})
        side_menu = Menu.create({'name': 'Side', 'parent_id': side_app.id, 'action': ref})
        main_first = Menu.create({'name': 'Main 1', 'parent_id': main_app.id, 'action': ref})
        Menu.create({'name': 'Main 2', 'parent_id': main_app.id, 'action': ref})
        menus = side_menu | main_first | Menu.search([('name', '=', 'Main 2')])
        picked = self.env['minimal_backend_theme.global_search']._pick_menu_by_model(
            menus, lambda menu: 'res.partner.category')
        self.assertEqual(picked, {'res.partner.category': main_first.id})

    def test_records_open_in_the_app_made_for_them(self):
        """An app whose main screen is the model (Contacts for contacts) wins
        over one listing it in more menus (Invoicing's customers, vendors...)."""
        Menu = self.env['ir.ui.menu']
        Action = self.env['ir.actions.act_window']
        tags = Action.create({'name': 'Tags', 'res_model': 'res.partner.category', 'view_mode': 'list,form'})
        other = Action.create({'name': 'Other', 'res_model': 'res.country', 'view_mode': 'list,form'})
        tags_ref = f'ir.actions.act_window,{tags.id}'
        # "Lister": main screen is countries, lists tags in two menus.
        lister = Menu.create({'name': 'Lister', 'sequence': 1})
        Menu.create({'name': 'Home', 'parent_id': lister.id, 'sequence': 1, 'action': f'ir.actions.act_window,{other.id}'})
        lister_tags = Menu.create({'name': 'Tags 1', 'parent_id': lister.id, 'sequence': 2, 'action': tags_ref})
        lister_tags2 = Menu.create({'name': 'Tags 2', 'parent_id': lister.id, 'sequence': 3, 'action': tags_ref})
        # "Owner": its main screen is tags, a single menu.
        owner = Menu.create({'name': 'Owner', 'sequence': 2})
        owner_tags = Menu.create({'name': 'Tags', 'parent_id': owner.id, 'action': tags_ref})
        picked = self.env['minimal_backend_theme.global_search']._pick_menu_by_model(
            lister_tags | lister_tags2 | owner_tags, lambda menu: 'res.partner.category')
        self.assertEqual(picked, {'res.partner.category': owner_tags.id})
