# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo import fields


@tagged('post_install', '-at_install')
class TestMenuLock(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestMenuLock, cls).setUpClass()

        # Create testing menus (top-level menus)
        cls.menu_1 = cls.env['ir.ui.menu'].create({
            'name': 'Lock Test Menu 1',
        })
        cls.menu_2 = cls.env['ir.ui.menu'].create({
            'name': 'Lock Test Menu 2',
        })

        # Find or create a test model (e.g. res.partner)
        cls.model_partner = cls.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)

        # Create window actions for testing
        cls.action_partner = cls.env['ir.actions.act_window'].create({
            'name': 'Partner Act Window',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
        })

        # Create test users
        cls.test_user = cls.env['res.users'].create({
            'name': 'Menu Lock Test User',
            'login': 'menu_lock_test_user',
            'email': 'menulock@test.com',
        })

    def test_01_single_password_onchange(self):
        """Test onchange methods for single password lock configuration."""
        # Instantiate in-memory record to test onchange logic
        user = self.env['res.users'].new({
            'name': 'Onchange Single User',
            'password_lock': 'single_password',
            'login_password': 'singlepassword123',
            'menus_to_lock_ids': [fields.Command.link(self.menu_1.id)],
        })

        # Trigger onchange of menus_to_lock_ids
        user._onchange_menus_to_lock_ids()

        # Verify that multi_lock_ids contains the linked menu and password
        self.assertEqual(len(user.multi_lock_ids), 1, "There should be 1 multi lock entry")
        self.assertEqual(user.multi_lock_ids[0].menus_id, self.menu_1)
        self.assertEqual(user.multi_lock_ids[0].password, 'singlepassword123')

        # Add an additional menu to menus_to_lock_ids and trigger onchange again
        user.menus_to_lock_ids = [fields.Command.link(self.menu_1.id), fields.Command.link(self.menu_2.id)]
        user._onchange_menus_to_lock_ids()

        self.assertEqual(len(user.multi_lock_ids), 2, "There should be 2 multi lock entries")
        self.assertEqual(user.multi_lock_ids.mapped('menus_id')._origin, self.menu_1 + self.menu_2)
        self.assertEqual(user.multi_lock_ids.mapped('password'), ['singlepassword123', 'singlepassword123'])

    def test_02_multi_password_onchange(self):
        """Test onchange methods for multi password lock configuration."""
        user = self.env['res.users'].new({
            'name': 'Onchange Multi User',
            'password_lock': 'multi_password',
        })

        # Add password locks to multi_lock_ids
        user.multi_lock_ids = [
            fields.Command.create({
                'menus_id': self.menu_1.id,
                'password': 'pwd1',
            }),
            fields.Command.create({
                'menus_id': self.menu_2.id,
                'password': 'pwd2',
            }),
        ]

        # Trigger onchange of multi_lock_ids
        user._onchange_multi_lock_ids()

        # Verify that menus_to_lock_ids is updated to include the menus from multi_lock_ids
        self.assertEqual(len(user.menus_to_lock_ids), 2)
        self.assertEqual(user.menus_to_lock_ids._origin, self.menu_1 + self.menu_2)


    def test_03_menu_lock_search_single(self):
        """Test menu_lock_search method for a user configured with a single password."""
        user = self.test_user
        user.write({
            'password_lock': 'single_password',
            'login_password': 'singlepassword123',
            'menus_to_lock_ids': [fields.Command.set([self.menu_1.id])],
            'models_to_lock_ids': [fields.Command.set([self.model_partner.id])],
        })
        # Save multi_lock_ids database records manually to mock the onchange write
        self.env['menu.password'].create({
            'menus_id': self.menu_1.id,
            'password': 'singlepassword123',
            'password_id': user.id,
        })

        # Call menu_lock_search for menu_1 (locked menu) and action_partner
        res = self.env['res.users'].menu_lock_search(user.id, action=self.action_partner.id, action_type='ir.actions.act_window')

        self.assertEqual(res['lock_type'], 'single_password')
        self.assertEqual(res['login_password'], 'singlepassword123')
        self.assertIn(self.menu_1.id, res['locked_menu_ids'])
        self.assertTrue(res['locked_models'])
        self.assertEqual(len(res['multi_lock_ids']), 1)
        self.assertEqual(res['multi_lock_ids'][0]['id'], self.menu_1.id)
        self.assertEqual(res['multi_lock_ids'][0]['password'], 'singlepassword123')

    def test_04_menu_lock_search_multi(self):
        """Test menu_lock_search method for a user configured with multiple passwords."""
        user = self.test_user
        user.write({
            'password_lock': 'multi_password',
            'menus_to_lock_ids': [fields.Command.set([self.menu_1.id, self.menu_2.id])],
        })
        self.env['menu.password'].create([
            {
                'menus_id': self.menu_1.id,
                'password': 'pwd1',
                'password_id': user.id,
            },
            {
                'menus_id': self.menu_2.id,
                'password': 'pwd2',
                'password_id': user.id,
            }
        ])

        # Call menu_lock_search without matching action_type
        res = self.env['res.users'].menu_lock_search(user.id, action=False, action_type=False)

        self.assertEqual(res['lock_type'], 'multi_password')
        self.assertFalse(res['locked_models'])
        self.assertIn(self.menu_1.id, res['locked_menu_ids'])
        self.assertIn(self.menu_2.id, res['locked_menu_ids'])
        self.assertEqual(len(res['multi_lock_ids']), 2)

        # Verify password mapping
        pwd_map = {item['id']: item['password'] for item in res['multi_lock_ids']}
        self.assertEqual(pwd_map[self.menu_1.id], 'pwd1')
        self.assertEqual(pwd_map[self.menu_2.id], 'pwd2')
