# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
"""Test suite for wishlist_product_website_backend module."""
import os

from odoo.modules.module import get_module_path
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'wishlist_product_website_backend')
class TestWishlistProductWebsiteBackend(TransactionCase):
    """Test suite verifying module installation, manifest metadata, backend
    views, menu action, security access rules, and wishlist records management.
    """

    @classmethod
    def setUpClass(cls):
        """Set up class test data for wishlist backend testing."""
        super().setUpClass()
        cls.module_path = get_module_path('wishlist_product_website_backend')
        cls.module = cls.env['ir.module.module'].search([
            ('name', '=', 'wishlist_product_website_backend'),
        ], limit=1)
        cls.website = cls.env['website'].search([], limit=1)

    def test_01_module_installation(self):
        """Verify wishlist_product_website_backend is loaded and installed."""
        self.assertTrue(
            self.module,
            "Module wishlist_product_website_backend must exist in ir.module.module.",
        )
        self.assertEqual(
            self.module.state,
            'installed',
            "Module wishlist_product_website_backend should be in installed state.",
        )

    def test_02_manifest_metadata(self):
        """Verify manifest completeness, category, license, and dependencies."""
        self.assertEqual(self.module.license, 'LGPL-3')
        self.assertEqual(self.module.category_id.name, 'Website')
        self.assertIn('Cybrosys', self.module.author)

        dependencies = [dep.name for dep in self.module.dependencies_id]
        self.assertIn('website_sale', dependencies)

    def test_03_views_and_action(self):
        """Verify backend wishlist views, window action, and reporting menu."""
        form_view = self.env.ref(
            'wishlist_product_website_backend.product_wishlist_view_form',
            raise_if_not_found=False,
        )
        self.assertTrue(form_view, "Form view must exist.")
        self.assertEqual(form_view.model, 'product.wishlist')

        tree_view = self.env.ref(
            'wishlist_product_website_backend.product_wishlist_view_tree',
            raise_if_not_found=False,
        )
        self.assertTrue(tree_view, "List view must exist.")
        self.assertEqual(tree_view.model, 'product.wishlist')

        search_view = self.env.ref(
            'wishlist_product_website_backend.product_wishlist_tree_search',
            raise_if_not_found=False,
        )
        self.assertTrue(search_view, "Search view must exist.")

        action = self.env.ref(
            'wishlist_product_website_backend.product_wishlist_action',
            raise_if_not_found=False,
        )
        self.assertTrue(action, "Window action must exist.")
        self.assertEqual(action.res_model, 'product.wishlist')
        self.assertIn('search_default_group_by_partner', action.context)

        menu = self.env.ref(
            'wishlist_product_website_backend.wishlist_product_menu',
            raise_if_not_found=False,
        )
        self.assertTrue(menu, "Wishlist backend menuitem must exist.")
        self.assertEqual(menu.parent_id, self.env.ref('website.menu_reporting'))

    def test_04_wishlist_records_and_views_rendering(self):
        """Verify wishlist creation, search domain filtering, and view rendering."""
        partner = self.env['res.partner'].create({
            'name': 'Test Wishlist Customer',
            'email': 'wishlist_customer@gmail.com',
        })
        product = self.env['product.product'].create({
            'name': 'Wishlist Sample Product',
            'list_price': 150.0,
            'is_published': True,
        })
        wishlist = self.env['product.wishlist'].create({
            'partner_id': partner.id,
            'product_id': product.id,
            'website_id': self.website.id,
            'price': product.list_price,
            'active': True,
        })
        self.assertTrue(wishlist.id, "Wishlist entry should be created.")
        self.assertEqual(wishlist.partner_id, partner)
        self.assertEqual(wishlist.product_id, product)

        # Verify form and list view rendering
        form_render = self.env['product.wishlist'].get_view(
            view_id=self.env.ref(
                'wishlist_product_website_backend.product_wishlist_view_form',
            ).id,
            view_type='form',
        )
        self.assertIn('partner_id', form_render['arch'])
        self.assertIn('product_id', form_render['arch'])

        list_render = self.env['product.wishlist'].get_view(
            view_id=self.env.ref(
                'wishlist_product_website_backend.product_wishlist_view_tree',
            ).id,
            view_type='list',
        )
        self.assertIn('partner_id', list_render['arch'])
        self.assertIn('product_id', list_render['arch'])

        # Verify search filter domain
        found = self.env['product.wishlist'].search([
            ('partner_id', '=', partner.id),
            ('product_id', '=', product.id),
        ])
        self.assertIn(wishlist, found)

    def test_05_menuitem_security_groups(self):
        """Verify wishlist menu restrictions to website designer/editor groups."""
        menu = self.env.ref(
            'wishlist_product_website_backend.wishlist_product_menu',
        )
        expected_groups = [
            self.env.ref('website.group_website_designer'),
            self.env.ref('website.group_website_restricted_editor'),
        ]
        for group in expected_groups:
            self.assertIn(group, menu.group_ids)

    def test_06_docs_and_assets(self):
        """Verify presence and non-empty status of all documentation and screenshots."""
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
        """Verify security access rules for product.wishlist."""
        group_designer = self.env.ref('website.group_website_designer')
        group_editor = self.env.ref('website.group_website_restricted_editor')

        group_field = (
            'group_ids'
            if 'group_ids' in self.env['res.users']._fields
            else 'groups_id'
        )
        base_user = self.env.ref('base.group_user')
        user_editor = self.env['res.users'].create({
            'name': 'Wishlist Editor User',
            'login': 'wishlist_editor_user@gmail.com',
            'email': 'wishlist_editor_user@gmail.com',
            group_field: [(6, 0, [base_user.id, group_editor.id])],
        })

        # Test read access for editor user
        wishlists_as_editor = self.env['product.wishlist'].with_user(
            user_editor,
        ).search([])
        self.assertIsNotNone(wishlists_as_editor)

        # Verify access rules exist in ir.access
        access_records = self.env['ir.access'].search([
            ('model_id.model', '=', 'product.wishlist'),
            ('group_id', 'in', [group_designer.id, group_editor.id]),
        ])
        self.assertTrue(
            access_records,
            "Access rules for product.wishlist and website editor should exist.",
        )
