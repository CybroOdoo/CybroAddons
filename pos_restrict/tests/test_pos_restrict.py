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
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged
from odoo.tools.safe_eval import safe_eval


@tagged('post_install', '-at_install')
class TestPosRestrict(TransactionCase):
    """Test suite for POS user restriction functionality and security rules."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_user_group = cls.env.ref('point_of_sale.group_pos_user')
        cls.pos_manager_group = cls.env.ref('point_of_sale.group_pos_manager')

        # Create Point of Sale configurations
        cls.pos_config_1 = cls.env['pos.config'].create({
            'name': 'Test POS Config 1',
        })
        cls.pos_config_2 = cls.env['pos.config'].create({
            'name': 'Test POS Config 2',
        })

        # Create an unrestricted POS user
        cls.unrestricted_user = cls.env['res.users'].create({
            'name': 'Unrestricted POS User',
            'login': 'unrestricted_pos_user',
            'email': 'unrestricted_pos_user@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id, cls.pos_user_group.id])],
        })

        # Create a restricted POS user assigned to pos_config_1
        cls.restricted_user = cls.env['res.users'].create({
            'name': 'Restricted POS User',
            'login': 'restricted_pos_user',
            'email': 'restricted_pos_user@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id, cls.pos_user_group.id])],
            'allowed_pos_ids': [(6, 0, [cls.pos_config_1.id])],
        })

        # Create a POS manager user
        cls.manager_user = cls.env['res.users'].create({
            'name': 'POS Manager User',
            'login': 'pos_manager_user',
            'email': 'pos_manager_user@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id, cls.pos_manager_group.id])],
            'show_users': True,
        })

    def test_01_unrestricted_pos_user_access(self):
        """Unrestricted POS user without allowed_pos_ids can access all POS configurations."""
        configs = self.env['pos.config'].with_user(self.unrestricted_user).search([
            ('id', 'in', (self.pos_config_1 | self.pos_config_2).ids)
        ])
        self.assertIn(self.pos_config_1, configs)
        self.assertIn(self.pos_config_2, configs)

    def test_02_restricted_pos_user_pos_config_access(self):
        """Restricted POS user can only access their allowed POS configuration."""
        configs = self.env['pos.config'].with_user(self.restricted_user).search([
            ('id', 'in', (self.pos_config_1 | self.pos_config_2).ids)
        ])
        self.assertIn(self.pos_config_1, configs)
        self.assertNotIn(self.pos_config_2, configs)

        # Trying to read disallowed POS config directly raises an AccessError
        with self.assertRaises(AccessError):
            self.pos_config_2.with_user(self.restricted_user).read(['name'])

    def test_03_restricted_pos_user_session_access(self):
        """Restricted POS user can only access sessions belonging to allowed POS configurations."""
        session_1 = self.env['pos.session'].create({
            'config_id': self.pos_config_1.id,
        })
        session_2 = self.env['pos.session'].create({
            'config_id': self.pos_config_2.id,
        })

        sessions = self.env['pos.session'].with_user(self.restricted_user).search([
            ('id', 'in', (session_1 | session_2).ids)
        ])
        self.assertIn(session_1, sessions)
        self.assertNotIn(session_2, sessions)

        with self.assertRaises(AccessError):
            session_2.with_user(self.restricted_user).read(['name'])

    def test_04_restricted_pos_user_order_access(self):
        """Restricted POS user can only access POS orders belonging to allowed POS configurations."""
        session_1 = self.env['pos.session'].create({
            'config_id': self.pos_config_1.id,
        })
        session_2 = self.env['pos.session'].create({
            'config_id': self.pos_config_2.id,
        })

        order_1 = self.env['pos.order'].create({
            'company_id': self.env.company.id,
            'session_id': session_1.id,
            'amount_tax': 0.0,
            'amount_total': 100.0,
            'amount_paid': 100.0,
            'amount_return': 0.0,
        })
        order_2 = self.env['pos.order'].create({
            'company_id': self.env.company.id,
            'session_id': session_2.id,
            'amount_tax': 0.0,
            'amount_total': 200.0,
            'amount_paid': 200.0,
            'amount_return': 0.0,
        })

        orders = self.env['pos.order'].with_user(self.restricted_user).search([
            ('id', 'in', (order_1 | order_2).ids)
        ])
        self.assertIn(order_1, orders)
        self.assertNotIn(order_2, orders)

        with self.assertRaises(AccessError):
            order_2.with_user(self.restricted_user).read(['name'])

    def test_05_allowed_pos_category_computation(self):
        """Verify computation of allowed POS categories and unlimited POS flag."""
        # Case A: User with no allowed_pos_ids has unlimited POS access
        self.assertTrue(self.unrestricted_user.has_unlimited_pos)
        self.assertFalse(self.unrestricted_user.allowed_pos_category_ids)

        # Case B: User assigned to POS without category limit has unlimited POS access
        self.pos_config_1.limit_categories = False
        self.restricted_user._compute_allowed_pos_categories()
        self.assertTrue(self.restricted_user.has_unlimited_pos)

        # Case C: User assigned to POS with limited categories
        pos_categ_a = self.env['pos.category'].create({'name': 'Category A'})
        pos_categ_b = self.env['pos.category'].create({'name': 'Category B'})
        self.pos_config_1.write({
            'limit_categories': True,
            'iface_available_categ_ids': [(6, 0, [pos_categ_a.id])],
        })
        self.restricted_user._compute_allowed_pos_categories()
        self.assertFalse(self.restricted_user.has_unlimited_pos)
        self.assertIn(pos_categ_a, self.restricted_user.allowed_pos_category_ids)
        self.assertNotIn(pos_categ_b, self.restricted_user.allowed_pos_category_ids)

    def test_06_product_category_restriction(self):
        """Verify product access restriction rule domain based on allowed POS categories."""
        pos_categ_allowed = self.env['pos.category'].create({'name': 'Allowed Category'})
        pos_categ_disallowed = self.env['pos.category'].create({'name': 'Disallowed Category'})

        product_allowed = self.env['product.template'].create({
            'name': 'Allowed Product',
            'available_in_pos': True,
            'pos_categ_ids': [(6, 0, [pos_categ_allowed.id])],
        })
        product_disallowed = self.env['product.template'].create({
            'name': 'Disallowed Product',
            'available_in_pos': True,
            'pos_categ_ids': [(6, 0, [pos_categ_disallowed.id])],
        })

        # Restrict user to pos_config_1 with only pos_categ_allowed
        self.pos_config_1.write({
            'limit_categories': True,
            'iface_available_categ_ids': [(6, 0, [pos_categ_allowed.id])],
        })
        self.restricted_user._compute_allowed_pos_categories()

        # Evaluate the security rule domain in the context of the restricted user
        rule = self.env.ref('point_of_sale.access_product_template_pos_user')
        eval_context = self.env['ir.access'].with_user(self.restricted_user)._eval_context()
        domain = safe_eval(rule.domain, eval_context)

        # Disallowed products are filtered out by the domain
        filtered_products = (product_allowed | product_disallowed).filtered_domain(domain)
        self.assertIn(product_allowed, filtered_products)
        self.assertNotIn(product_disallowed, filtered_products)

        # When evaluated for an unrestricted user, the domain allows all
        eval_context_unrestricted = self.env['ir.access'].with_user(self.unrestricted_user)._eval_context()
        unrestricted_domain = safe_eval(rule.domain, eval_context_unrestricted)
        self.assertEqual(unrestricted_domain, [(1, '=', 1)])

    def test_07_users_allowed_ids_computation(self):
        """Verify computation of users_allowed_ids on pos.config."""
        # Ensure restricted_user is assigned to pos_config_1
        self.restricted_user.allowed_pos_ids = [(6, 0, [self.pos_config_1.id])]

        # When viewing with show_users enabled
        self.manager_user.show_users = True
        self.pos_config_1.invalidate_recordset(['users_allowed_ids'])
        config_with_manager = self.pos_config_1.with_user(self.manager_user)
        self.assertIn(self.restricted_user, config_with_manager.users_allowed_ids)
        self.assertNotIn(self.unrestricted_user, config_with_manager.users_allowed_ids)

        # When viewing with show_users disabled
        self.manager_user.show_users = False
        self.pos_config_1.invalidate_recordset(['users_allowed_ids'])
        config_with_manager_hidden = self.pos_config_1.with_user(self.manager_user)
        self.assertFalse(config_with_manager_hidden.users_allowed_ids)
