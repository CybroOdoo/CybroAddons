# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install')
class TestInfinitoTheme(TransactionCase):
    def test_settings_preserve_false_and_schedule(self):
        settings = self.env['res.config.settings'].create({
            'is_sidebar_icon': False,
            'is_sidebar_name': False,
            'is_fullscreen_app': True,
            'dark_start': 20.5,
            'dark_end': 6.25,
        })
        settings.set_values()
        defaults = self.env['res.config.settings'].default_get([
            'is_sidebar_icon', 'is_sidebar_name', 'is_fullscreen_app',
            'dark_start', 'dark_end',
        ])
        self.assertFalse(defaults['is_sidebar_icon'])
        self.assertFalse(defaults['is_sidebar_name'])
        self.assertTrue(defaults['is_fullscreen_app'])
        self.assertEqual(defaults['dark_start'], 20.5)
        self.assertEqual(defaults['dark_end'], 6.25)

    def test_private_bookmarks(self):
        owner = new_test_user(self.env, login='infinito_owner', groups='base.group_user')
        other = new_test_user(self.env, login='infinito_other', groups='base.group_user')
        bookmark = self.env['infinito.menu.bookmark'].with_user(owner).create({
            'name': 'Private bookmark', 'user_id': owner.id, 'url': '/odoo',
        })
        self.assertFalse(bookmark.with_user(other).search([('id', '=', bookmark.id)]))
        with self.assertRaises(AccessError):
            bookmark.with_user(other).write({'name': 'Changed'})

    def test_missing_recent_menu(self):
        recent = self.env['recent.apps'].create({'app_id': 0, 'user_id': self.env.uid})
        self.assertFalse(recent.name)
        self.assertFalse(recent.icon)
