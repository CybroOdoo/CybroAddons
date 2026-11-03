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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestRestrictPricelistUser(common.TransactionCase):
    """Test suite for restrict_pricelist_user module covering configuration,
    user restrictions, pricelist search overrides, and view structures."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Save initial state of the parameter
        cls.initial_restricted = cls.env['ir.config_parameter'].sudo().get_bool(
            'restrict_pricelist_user.is_restricted'
        )

        # Create test pricelists
        cls.pricelist_1 = cls.env['product.pricelist'].create({'name': 'Test Pricelist 1'})
        cls.pricelist_2 = cls.env['product.pricelist'].create({'name': 'Test Pricelist 2'})
        cls.pricelist_3 = cls.env['product.pricelist'].create({'name': 'Test Pricelist 3'})

        # Groups for sales user
        group_sale = cls.env.ref('sales_team.group_sale_salesman')
        group_internal = cls.env.ref('base.group_user')

        # User restricted to pricelist 1 and 2
        cls.user_restricted = cls.env['res.users'].create({
            'name': 'Restricted Sales User',
            'login': 'restricted_sales_user',
            'email': 'restricted@example.com',
            'group_ids': [(6, 0, [group_sale.id, group_internal.id])],
            'pricelist_ids': [(6, 0, [cls.pricelist_1.id, cls.pricelist_2.id])],
        })

        # User restricted to pricelist 3 only
        cls.user_single_pl = cls.env['res.users'].create({
            'name': 'Single Pricelist User',
            'login': 'single_pl_user',
            'email': 'single_pl@example.com',
            'group_ids': [(6, 0, [group_sale.id, group_internal.id])],
            'pricelist_ids': [(6, 0, [cls.pricelist_3.id])],
        })

        # User with no pricelists assigned
        cls.user_unassigned = cls.env['res.users'].create({
            'name': 'Unassigned Pricelist User',
            'login': 'unassigned_pl_user',
            'email': 'unassigned@example.com',
            'group_ids': [(6, 0, [group_sale.id, group_internal.id])],
        })

    def tearDown(self):
        super().tearDown()
        self.env['ir.config_parameter'].sudo().set_bool(
            'restrict_pricelist_user.is_restricted', self.initial_restricted
        )

    def test_01_views_structure(self):
        """Verify inherited settings and user views exist and load correctly."""
        settings_view = self.env.ref('restrict_pricelist_user.res_config_settings_view_form')
        user_view = self.env.ref('restrict_pricelist_user.view_users_form')
        self.assertTrue(settings_view, "res_config_settings_view_form must exist.")
        self.assertTrue(user_view, "view_users_form must exist.")

        user_views = self.env['res.users'].get_views([(user_view.id, 'form')])
        self.assertIn('form', user_views.get('views', {}))

    def test_02_disabled_restriction_all_visible(self):
        """Verify that when restriction is disabled, all pricelists are visible to users."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'restrict_pricelist_user.is_restricted', False
        )
        self.user_restricted._compute_is_restricted()
        self.assertFalse(self.user_restricted.is_restricted)

        # Search as restricted user: all test pricelists should be returned
        visible = self.env['product.pricelist'].with_user(self.user_restricted).search([
            ('id', 'in', [self.pricelist_1.id, self.pricelist_2.id, self.pricelist_3.id])
        ])
        self.assertEqual(len(visible), 3)
        self.assertIn(self.pricelist_1, visible)
        self.assertIn(self.pricelist_2, visible)
        self.assertIn(self.pricelist_3, visible)

    def test_03_enabled_restriction_user_restricted(self):
        """Verify that when restriction is enabled, user sees only assigned pricelists."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'restrict_pricelist_user.is_restricted', True
        )
        self.user_restricted._compute_is_restricted()
        self.assertTrue(self.user_restricted.is_restricted)

        # Search as restricted user: only pricelist 1 and 2 should be returned
        visible = self.env['product.pricelist'].with_user(self.user_restricted).search([
            ('id', 'in', [self.pricelist_1.id, self.pricelist_2.id, self.pricelist_3.id])
        ])
        self.assertEqual(len(visible), 2)
        self.assertIn(self.pricelist_1, visible)
        self.assertIn(self.pricelist_2, visible)
        self.assertNotIn(self.pricelist_3, visible)

    def test_04_enabled_restriction_single_pricelist(self):
        """Verify user with single assigned pricelist sees only that pricelist."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'restrict_pricelist_user.is_restricted', True
        )
        visible = self.env['product.pricelist'].with_user(self.user_single_pl).search([
            ('id', 'in', [self.pricelist_1.id, self.pricelist_2.id, self.pricelist_3.id])
        ])
        self.assertEqual(len(visible), 1)
        self.assertEqual(visible, self.pricelist_3)

    def test_05_enabled_restriction_unassigned_user_has_all_access(self):
        """Verify user without any assigned pricelists can access all pricelists."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'restrict_pricelist_user.is_restricted', True
        )
        self.user_unassigned._compute_is_restricted()
        self.assertTrue(self.user_unassigned.is_restricted)
        self.assertFalse(self.user_unassigned.pricelist_ids)

        visible = self.env['product.pricelist'].with_user(self.user_unassigned).search([
            ('id', 'in', [self.pricelist_1.id, self.pricelist_2.id, self.pricelist_3.id])
        ])
        self.assertEqual(len(visible), 3)

    def test_06_superuser_bypass(self):
        """Verify superuser / sudo bypasses pricelist restriction."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'restrict_pricelist_user.is_restricted', True
        )
        su_visible = self.env['product.pricelist'].sudo().search([
            ('id', 'in', [self.pricelist_1.id, self.pricelist_2.id, self.pricelist_3.id])
        ])
        self.assertEqual(len(su_visible), 3)

    def test_07_existing_domain_preserved(self):
        """Verify search combines caller's domain with restriction domain."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'restrict_pricelist_user.is_restricted', True
        )
        # Search specifically for pricelist 1 by name
        results = self.env['product.pricelist'].with_user(self.user_restricted).search([
            ('name', '=', 'Test Pricelist 1')
        ])
        self.assertEqual(len(results), 1)
        self.assertEqual(results, self.pricelist_1)

        # Search specifically for pricelist 3 by name (not assigned to this user)
        results_hidden = self.env['product.pricelist'].with_user(self.user_restricted).search([
            ('name', '=', 'Test Pricelist 3')
        ])
        self.assertEqual(len(results_hidden), 0)

    def test_08_res_config_settings_flow(self):
        """Verify enabling and disabling via res.config.settings updates config parameter."""
        # Enable in settings
        settings_on = self.env['res.config.settings'].create({'is_restricted': True})
        settings_on.set_values()
        self.assertTrue(
            self.env['ir.config_parameter'].sudo().get_bool('restrict_pricelist_user.is_restricted')
        )

        # Disable in settings
        settings_off = self.env['res.config.settings'].create({'is_restricted': False})
        settings_off.set_values()
        self.assertFalse(
            self.env['ir.config_parameter'].sudo().get_bool('restrict_pricelist_user.is_restricted')
        )

    def test_09_user_form_tab_invisibility_condition(self):
        """Verify form view tab invisibility evaluation (invisible='is_restricted == False')."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'restrict_pricelist_user.is_restricted', False
        )
        self.user_restricted._compute_is_restricted()
        self.assertTrue(
            self.user_restricted.is_restricted == False,
            "Notebook tab should be invisible when is_restricted is False",
        )

        self.env['ir.config_parameter'].sudo().set_bool(
            'restrict_pricelist_user.is_restricted', True
        )
        self.user_restricted._compute_is_restricted()
        self.assertFalse(
            self.user_restricted.is_restricted == False,
            "Notebook tab should be visible when is_restricted is True",
        )

    def test_10_multi_user_is_restricted_compute(self):
        """Verify _compute_is_restricted on multi-record user recordset."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'restrict_pricelist_user.is_restricted', True
        )
        users = self.user_restricted + self.user_single_pl + self.user_unassigned
        users._compute_is_restricted()
        self.assertTrue(all(u.is_restricted for u in users))

        self.env['ir.config_parameter'].sudo().set_bool(
            'restrict_pricelist_user.is_restricted', False
        )
        users._compute_is_restricted()
        self.assertFalse(any(u.is_restricted for u in users))
