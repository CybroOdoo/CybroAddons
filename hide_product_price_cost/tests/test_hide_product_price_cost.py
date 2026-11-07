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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
"""Test suite for hide_product_price_cost module."""
import os

from odoo.modules.module import get_module_path
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'hide_product_price_cost')
class TestHideProductPriceCost(TransactionCase):
    """Test suite verifying module installation, manifest metadata, security
    groups, view inheritance, and documentation files for Hide Product Price
    and Cost.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test environment and module references."""
        super().setUpClass()
        cls.module_path = get_module_path('hide_product_price_cost')
        cls.module = cls.env['ir.module.module'].search([
            ('name', '=', 'hide_product_price_cost'),
        ], limit=1)

    def test_01_module_installation(self):
        """Verify hide_product_price_cost is registered and installed."""
        self.assertTrue(
            self.module,
            "Module hide_product_price_cost must exist in ir.module.module.",
        )
        self.assertEqual(
            self.module.state,
            'installed',
            "Module hide_product_price_cost should be in installed state.",
        )

    def test_02_manifest_metadata(self):
        """Verify manifest completeness, category, license, and author."""
        self.assertEqual(self.module.license, 'LGPL-3')
        self.assertEqual(self.module.category_id.name, 'Sales')
        self.assertIn('Cybrosys', self.module.author)

        dependencies = [dep.name for dep in self.module.dependencies_id]
        self.assertIn('base', dependencies)
        self.assertIn('product', dependencies)

    def test_03_security_groups(self):
        """Verify security groups for showing product price and cost exist."""
        price_group = self.env.ref(
            'hide_product_price_cost.hide_product_price_cost_group_user_show_product_price',
            raise_if_not_found=False,
        )
        self.assertTrue(
            price_group,
            "Security group 'Show Product Price' must exist.",
        )
        self.assertEqual(price_group.name, 'Show Product Price')

        cost_group = self.env.ref(
            'hide_product_price_cost.hide_product_price_cost_group_user_show_product_cost',
            raise_if_not_found=False,
        )
        self.assertTrue(
            cost_group,
            "Security group 'Show Product Cost' must exist.",
        )
        self.assertEqual(cost_group.name, 'Show Product Cost')

    def test_04_views_inheritance(self):
        """Verify view inheritance records are loaded and active."""
        expected_views = [
            'hide_product_price_cost.product_template_form_view',
            'hide_product_price_cost.product_template_kanban_view',
            'hide_product_price_cost.product_template_tree_view',
            'hide_product_price_cost.product_normal_form_view',
            'hide_product_price_cost.product_kanban_view',
            'hide_product_price_cost.product_product_tree_view',
        ]
        for view_xml_id in expected_views:
            view = self.env.ref(view_xml_id, raise_if_not_found=False)
            self.assertTrue(view, f"Inherited view {view_xml_id} must exist.")
            self.assertTrue(view.active, f"View {view_xml_id} should be active.")

    def test_05_field_visibility_per_user_group(self):
        """Verify user without price/cost groups cannot see price/cost fields,
        and user with groups can see them.
        """
        price_group = self.env.ref(
            'hide_product_price_cost.hide_product_price_cost_group_user_show_product_price',
        )
        cost_group = self.env.ref(
            'hide_product_price_cost.hide_product_price_cost_group_user_show_product_cost',
        )
        group_user = self.env.ref('base.group_user')

        test_user = self.env['res.users'].create({
            'name': 'Test Restricted Product User',
            'login': 'test_restricted_product_user',
            'email': 'restricted_user@gmail.com',
            'group_ids': [(6, 0, [group_user.id])],
        })

        # Test view with restricted user
        env_restricted = self.env(user=test_user)
        arch_tmpl = env_restricted['product.template'].get_view(
            view_type='form',
        )['arch']
        # When user lacks groups, fields protected with groups are omitted in get_view
        self.assertNotIn(
            'name="list_price"',
            arch_tmpl,
            "list_price should be hidden in form view for user without price group.",
        )
        self.assertNotIn(
            'name="standard_price"',
            arch_tmpl,
            "standard_price should be hidden in form view for user without cost group.",
        )

        # Grant price group
        test_user.write({'group_ids': [(4, price_group.id)]})
        arch_with_price = self.env(user=test_user)['product.template'].get_view(
            view_type='form',
        )['arch']
        self.assertIn(
            'name="list_price"',
            arch_with_price,
            "list_price should be visible once price group is granted.",
        )
        self.assertNotIn(
            'name="standard_price"',
            arch_with_price,
            "standard_price should remain hidden until cost group is granted.",
        )

        # Grant cost group
        test_user.write({'group_ids': [(4, cost_group.id)]})
        arch_with_both = self.env(user=test_user)['product.template'].get_view(
            view_type='form',
        )['arch']
        self.assertIn(
            'name="list_price"',
            arch_with_both,
            "list_price should be visible with both groups granted.",
        )
        self.assertIn(
            'name="standard_price"',
            arch_with_both,
            "standard_price should be visible with both groups granted.",
        )

    def test_06_docs_and_assets(self):
        """Verify documentation, icons, banner, and screenshots exist."""
        self.assertTrue(self.module_path, "Module path must exist.")
        expected_files = [
            'README.rst',
            'doc/RELEASE_NOTES.md',
            'static/description/index.html',
            'static/description/icon.png',
            'static/description/banner.jpg',
            'static/description/assets/screenshots/1.png',
            'static/description/assets/screenshots/2.png',
            'static/description/assets/screenshots/3.png',
            'static/description/assets/screenshots/4.png',
            'static/description/assets/screenshots/5.png',
            'static/description/assets/screenshots/6.png',
            'static/description/assets/screenshots/7.png',
            'static/description/assets/screenshots/8.png',
            'static/description/assets/screenshots/9.png',
        ]
        for rel_path in expected_files:
            full_path = os.path.join(self.module_path, rel_path)
            self.assertTrue(
                os.path.isfile(full_path),
                f"Required asset or document '{rel_path}' must exist on disk.",
            )
            self.assertGreater(
                os.path.getsize(full_path),
                0,
                f"File '{rel_path}' must not be empty.",
            )

    def test_07_access_rules(self):
        """Verify access rules defined in security/ir.access.csv."""
        price_group = self.env.ref(
            'hide_product_price_cost.hide_product_price_cost_group_user_show_product_price',
        )
        cost_group = self.env.ref(
            'hide_product_price_cost.hide_product_price_cost_group_user_show_product_cost',
        )
        tmpl_access_price = self.env['ir.access'].search([
            ('model_id.model', '=', 'product.template'),
            ('group_id', '=', price_group.id),
        ])
        self.assertTrue(
            tmpl_access_price,
            "Access rule for product.template and price group must exist.",
        )
        tmpl_access_cost = self.env['ir.access'].search([
            ('model_id.model', '=', 'product.template'),
            ('group_id', '=', cost_group.id),
        ])
        self.assertTrue(
            tmpl_access_cost,
            "Access rule for product.template and cost group must exist.",
        )
        product_access_price = self.env['ir.access'].search([
            ('model_id.model', '=', 'product.product'),
            ('group_id', '=', price_group.id),
        ])
        self.assertTrue(
            product_access_price,
            "Access rule for product.product and price group must exist.",
        )
        product_access_cost = self.env['ir.access'].search([
            ('model_id.model', '=', 'product.product'),
            ('group_id', '=', cost_group.id),
        ])
        self.assertTrue(
            product_access_cost,
            "Access rule for product.product and cost group must exist.",
        )
