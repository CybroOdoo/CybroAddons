# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestMenuLock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(cls.env, login='menu_lock_test')
        cls.other = new_test_user(cls.env, login='menu_lock_other')
        cls.action = cls.env['ir.actions.act_window'].create({
            'name': 'Partners', 'res_model': 'res.partner',
        })
        cls.menu = cls.env['ir.ui.menu'].create({
            'name': 'Lock Test', 'action': f'ir.actions.act_window,{cls.action.id}',
        })
        cls.client = cls.env['res.users'].with_user(cls.user)

    def test_shared_password_is_private_and_scoped_to_user(self):
        self.user.write({
            'password_lock': 'single_password',
            'login_password': 'shared secret',
            'menus_to_lock_ids': [Command.set(self.menu.ids)],
        })
        self.assertTrue(self.client.menu_lock_required(self.menu.id))
        self.assertFalse(self.client.verify_menu_lock(self.menu.id, 'wrong'))
        self.assertTrue(self.client.verify_menu_lock(self.menu.id, 'shared secret'))
        self.assertFalse(self.client.with_user(self.other).menu_lock_required(self.menu.id))
        self.assertFalse(self.user.login_password)
        self.assertNotEqual(self.user.menu_lock_hash, 'shared secret')
        for field in ['menu_lock_hash', 'login_password']:
            with self.assertRaises(AccessError):
                self.user.with_user(self.other).read([field])

    def test_individual_password(self):
        self.user.password_lock = 'multi_password'
        line = self.env['menu.password'].create({
            'password_id': self.user.id, 'menus_id': self.menu.id, 'password': 'first',
        })
        self.assertFalse(line.password)
        self.assertTrue(line.has_password)
        self.assertEqual(line.password_length, 5)
        self.assertTrue(self.client.verify_menu_lock(self.menu.id, 'first'))
        line.password = 'second'
        self.assertEqual(line.password_length, 6)
        self.assertFalse(self.client.verify_menu_lock(self.menu.id, 'first'))
        self.assertTrue(self.client.verify_menu_lock(self.menu.id, 'second'))
        with self.assertRaises(AccessError):
            line.with_user(self.other).read(['menu_lock_hash'])
        with self.assertRaises(AccessError):
            line.with_user(self.other).write({'password': 'replacement'})
        line.password = False
        self.assertFalse(line.has_password)
        self.assertEqual(line.password_length, 0)
        self.assertFalse(self.client.verify_menu_lock(self.menu.id, 'second'))

    def test_model_lock_without_menu_password(self):
        self.user.models_to_lock_ids = self.env['ir.model']._get('res.partner')
        self.assertTrue(self.client.menu_lock_required(self.menu.id))
        self.assertFalse(self.client.verify_menu_lock(self.menu.id, ''))
        self.user.login_password = 'model secret'
        self.assertTrue(self.client.verify_menu_lock(self.menu.id, 'model secret'))
