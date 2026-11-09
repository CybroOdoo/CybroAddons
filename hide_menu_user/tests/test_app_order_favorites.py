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
from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestAppOrderFavorites(TransactionCase):
    """Test menu profiles (app order, team shortcuts) and favourite menus."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.group_user = cls.env.ref('base.group_user')
        cls.Menu = cls.env['ir.ui.menu']
        cls.Profile = cls.env['hide.menu.profile']
        cls.Favorite = cls.env['hide.menu.favorite']

        # Existing profiles would interfere with the matching tests.
        cls.Profile.search([]).action_archive()

        cls.action = cls.env['ir.actions.act_window'].create({
            'name': 'Test Action',
            'res_model': 'res.users',
            'view_mode': 'list',
        })
        action_ref = f'ir.actions.act_window,{cls.action.id}'
        cls.app_a = cls.Menu.create({'name': 'Test App A', 'action': action_ref})
        cls.app_b = cls.Menu.create({'name': 'Test App B', 'action': action_ref})
        cls.sub_menu = cls.Menu.create({
            'name': 'Test Sub Menu',
            'parent_id': cls.app_a.id,
            'action': action_ref,
        })

        cls.team_group = cls.env['res.groups'].create({'name': 'Hide Menu Team'})
        cls.user = cls.env['res.users'].create({
            'name': 'Team User',
            'login': 'hide_menu_team_user',
            'group_ids': [Command.set([cls.group_user.id, cls.team_group.id])],
        })
        cls.other_user = cls.env['res.users'].create({
            'name': 'Other User',
            'login': 'hide_menu_other_user',
            'group_ids': [Command.set([cls.group_user.id])],
        })

    def _root_children(self, user):
        self.env.transaction.invalidate_ormcache()
        return self.Menu.with_user(user).load_menus(False)['root']['children']

    def _assert_before(self, children, first, second):
        self.assertLess(children.index(first.id), children.index(second.id))

    def test_01_profile_matching(self):
        """A group profile applies to members only; an empty one to all."""
        team = self.Profile.create({
            'name': 'Team', 'sequence': 1,
            'group_ids': [Command.link(self.team_group.id)]})
        everyone = self.Profile.create({'name': 'Everyone', 'sequence': 2})
        self.assertEqual(self.Profile._get_for_user(self.user), team)
        self.assertEqual(self.Profile._get_for_user(self.other_user), everyone)
        portal = self.env['res.users'].create({
            'name': 'Portal', 'login': 'hide_menu_portal',
            'group_ids': [Command.set([self.env.ref('base.group_portal').id])]})
        self.assertFalse(self.Profile._get_for_user(portal))

    def test_02_profile_app_order(self):
        """The profile order is applied to the apps, without touching the
        cached result of other users."""
        self.assertLess(self.app_a.id, self.app_b.id)
        self._assert_before(self._root_children(self.user), self.app_a, self.app_b)
        self.Profile.create({
            'name': 'Team',
            'group_ids': [Command.link(self.team_group.id)],
            'app_ids': [
                Command.create({'menu_id': self.app_b.id, 'sequence': 1}),
                Command.create({'menu_id': self.app_a.id, 'sequence': 2}),
            ],
        })
        children = self._root_children(self.user)
        self.assertEqual(children[:2], [self.app_b.id, self.app_a.id])
        self._assert_before(self._root_children(self.other_user), self.app_a, self.app_b)

    def test_03_personal_order_wins(self):
        """A personal order overrides the profile; clearing it restores it."""
        self.Profile.create({
            'name': 'Team',
            'app_ids': [Command.create({'menu_id': self.app_b.id})],
        })
        settings = self.env['res.users.settings']._find_or_create_for_user(self.user)
        settings.with_user(self.user).set_res_users_settings(
            {'hide_menu_app_order': [self.app_a.id, self.app_b.id]})
        self.assertEqual(self._root_children(self.user)[:2], [self.app_a.id, self.app_b.id])
        settings.with_user(self.user).set_res_users_settings({'hide_menu_app_order': False})
        self.assertEqual(self._root_children(self.user)[0], self.app_b.id)

    def test_04_add_missing_apps(self):
        """'Add all apps' lists every app once, after the existing ones."""
        profile = self.Profile.create({
            'name': 'Team',
            'app_ids': [Command.create({'menu_id': self.app_b.id, 'sequence': 5})],
        })
        profile.action_add_missing_apps()
        self.assertEqual(profile.app_ids[0].menu_id, self.app_b)
        self.assertIn(self.app_a, profile.app_ids.menu_id)
        self.assertNotIn(self.sub_menu, profile.app_ids.menu_id)
        profile.action_add_missing_apps()
        self.assertEqual(len(profile.app_ids), len(set(profile.app_ids.menu_id.ids)))

    def test_05_toggle_favorite(self):
        """Users star and un-star menus they can see."""
        Favorite = self.Favorite.with_user(self.user)
        self.assertTrue(Favorite.toggle_star(self.sub_menu.id))
        self.assertEqual(Favorite.get_starred_menu_ids()['personal'], [self.sub_menu.id])
        self.assertFalse(Favorite.toggle_star(self.sub_menu.id))
        self.assertFalse(Favorite.get_starred_menu_ids()['personal'])

    def test_06_cannot_star_hidden_menu(self):
        """A menu hidden from the user cannot be starred."""
        self.user.hide_menu_ids = [Command.link(self.sub_menu.id)]
        self.env.transaction.invalidate_ormcache()
        with self.assertRaises(UserError):
            self.Favorite.with_user(self.user).toggle_star(self.sub_menu.id)

    def test_07_hidden_favorites_and_shortcuts_are_filtered(self):
        """Favourites and team shortcuts the user cannot see are dropped."""
        self.Profile.create({
            'name': 'Team',
            'shortcut_menu_ids': [Command.set([self.app_a.id, self.app_b.id])],
        })
        Favorite = self.Favorite.with_user(self.user)
        Favorite.toggle_star(self.sub_menu.id)
        self.app_b.restrict_user_ids = [Command.link(self.user.id)]
        self.sub_menu.restrict_user_ids = [Command.link(self.user.id)]
        self.env.transaction.invalidate_ormcache()
        result = Favorite.get_starred_menu_ids()
        self.assertEqual(result['personal'], [])
        self.assertEqual(result['shared'], [self.app_a.id])

    def test_08_favorites_are_private(self):
        """A user cannot read another user's favourites."""
        favorite = self.Favorite.create({
            'user_id': self.other_user.id, 'menu_id': self.sub_menu.id})
        self.assertFalse(self.Favorite.with_user(self.user).search(
            [('id', '=', favorite.id)]))
        with self.assertRaises(AccessError), mute_logger('odoo.models'):
            favorite.with_user(self.user).read(['menu_id'])
