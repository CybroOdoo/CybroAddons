# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana J(<https://www.cybrosys.com>)
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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestMenuLock(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.parent_menu_1 = cls.env['ir.ui.menu'].create({
            'name': 'Menu Lock Test 1',
        })
        cls.parent_menu_2 = cls.env['ir.ui.menu'].create({
            'name': 'Menu Lock Test 2',
        })
        cls.user = cls.env['res.users'].create({
            'name': 'Menu Lock User',
            'login': 'menu.lock.user@example.com',
            'password_lock': 'single_password',
            'login_password': 'secret123',
            'menus_to_lock_ids': [(6, 0, [cls.parent_menu_1.id, cls.parent_menu_2.id])],
        })

    def test_onchange_menus_to_lock_ids_creates_matching_lock_lines(self):
        self.user._onchange_menus_to_lock_ids()
        self.assertEqual(
            self.user.multi_lock_ids.mapped('menus_id'),
            self.parent_menu_1 | self.parent_menu_2,
        )
        self.assertEqual(
            self.user.multi_lock_ids.mapped('password'),
            ['secret123', 'secret123'],
        )

    def test_menu_lock_search_returns_multi_lock_payload(self):
        self.user._onchange_menus_to_lock_ids()
        result = self.env['res.users'].menu_lock_search([self.user.id])

        self.assertEqual(
            result,
            {
                'multi_lock_ids': [
                    {
                        'id': self.parent_menu_1.id,
                        'password': 'secret123',
                    },
                    {
                        'id': self.parent_menu_2.id,
                        'password': 'secret123',
                    },
                ]
            },
        )
