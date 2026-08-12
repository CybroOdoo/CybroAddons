# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Cybrosys Techno Solutions (odoo@cybrosys.com)
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
import logging
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestWishlistBackend(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestWishlistBackend, cls).setUpClass()
        _logger.info("Setting up TestWishlistBackend environment")

        # Create test partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer Wishlist',
            'email': 'test_wishlist@example.com',
        })

        # Create test product
        cls.product = cls.env['product.product'].create({
            'name': 'Test Wishlist Product',
            'type': 'consu',
            'list_price': 100.0,
        })

        # Get or create website
        cls.website = cls.env['website'].search([], limit=1)
        if not cls.website:
            cls.website = cls.env['website'].create({
                'name': 'Test Website',
            })

        # Create wishlist record
        cls.wishlist = cls.env['product.wishlist'].create({
            'partner_id': cls.partner.id,
            'product_id': cls.product.id,
            'website_id': cls.website.id,
            'active': True,
        })

        _logger.info("setUpClass completed successfully for TestWishlistBackend")

    def test_01_wishlist_creation_and_fields(self):
        """Test wishlist product creation and field values in backend."""
        _logger.info("Running test_01_wishlist_creation_and_fields")

        self.assertTrue(self.wishlist.id, "Wishlist record should be created successfully")
        self.assertEqual(self.wishlist.partner_id, self.partner, "Wishlist partner should match created partner")
        self.assertEqual(self.wishlist.product_id, self.product, "Wishlist product should match created product")
        self.assertEqual(self.wishlist.website_id, self.website, "Wishlist website should match test website")
        self.assertTrue(self.wishlist.active, "Wishlist record should be active by default")

        # Deactivate wishlist item
        self.wishlist.write({'active': False})
        self.assertFalse(self.wishlist.active, "Wishlist active status should update to False")
        _logger.info("Wishlist creation and field values validated successfully")

    def test_02_wishlist_backend_views_and_action(self):
        """Test backend views and window action defined in XML."""
        _logger.info("Running test_02_wishlist_backend_views_and_action")

        # Validate Form View definition
        form_view = self.env.ref('wishlist_product_website_backend.product_wishlist_view_form', raise_if_not_found=False)
        self.assertIsNotNone(form_view, "Form view 'product_wishlist_view_form' should exist")
        self.assertEqual(form_view.model, 'product.wishlist', "Form view model should be product.wishlist")

        # Validate Tree/List View definition
        tree_view = self.env.ref('wishlist_product_website_backend.product_wishlist_view_tree', raise_if_not_found=False)
        self.assertIsNotNone(tree_view, "Tree view 'product_wishlist_view_tree' should exist")
        self.assertEqual(tree_view.model, 'product.wishlist', "Tree view model should be product.wishlist")

        # Validate Search View definition
        search_view = self.env.ref('wishlist_product_website_backend.product_wishlist_tree_search', raise_if_not_found=False)
        self.assertIsNotNone(search_view, "Search view 'product_wishlist_tree_search' should exist")
        self.assertEqual(search_view.model, 'product.wishlist', "Search view model should be product.wishlist")

        # Validate Window Action
        action = self.env.ref('wishlist_product_website_backend.product_wishlist_action', raise_if_not_found=False)
        self.assertIsNotNone(action, "Window action 'product_wishlist_action' should exist")
        self.assertEqual(action.res_model, 'product.wishlist', "Action res_model should be product.wishlist")
        _logger.info("Backend views and action validated successfully")

    def test_03_wishlist_backend_menu(self):
        """Test backend menu item structure and security groups."""
        _logger.info("Running test_03_wishlist_backend_menu")

        menu = self.env.ref('wishlist_product_website_backend.wishlist_product_menu', raise_if_not_found=False)
        self.assertIsNotNone(menu, "Menu 'wishlist_product_menu' should exist")
        self.assertEqual(menu.name, "Wishlist Product", "Menu name should match 'Wishlist Product'")

        # Verify parent menu
        parent_menu = self.env.ref('website.menu_reporting', raise_if_not_found=False)
        if parent_menu:
            self.assertEqual(menu.parent_id, parent_menu, "Parent menu should be website.menu_reporting")

        # Verify groups assigned to menu
        group_designer = self.env.ref('website.group_website_designer', raise_if_not_found=False)
        group_editor = self.env.ref('website.group_website_restricted_editor', raise_if_not_found=False)
        expected_groups = {g for g in [group_designer, group_editor] if g}

        menu_groups = set(menu.group_ids)
        for expected_group in expected_groups:
            self.assertIn(expected_group, menu_groups, f"Menu should belong to group {expected_group.name}")

        _logger.info("Backend menu item and security groups validated successfully")

    def test_04_wishlist_search_and_groupby(self):
        """Test searching and grouping records for wishlist products in backend."""
        _logger.info("Running test_04_wishlist_search_and_groupby")

        # Search by product name
        domain = ['|', ('product_id.name', 'ilike', 'Test Wishlist'), ('partner_id.name', 'ilike', 'Test Wishlist')]
        results = self.env['product.wishlist'].search(domain)
        self.assertIn(self.wishlist, results, "Search should return the matching wishlist record")

        # Group by partner_id
        grouped_by_partner = self.env['product.wishlist']._read_group(
            domain=[('id', '=', self.wishlist.id)],
            groupby=['partner_id']
        )
        self.assertTrue(len(grouped_by_partner) > 0, "Group by partner should yield results")
        self.assertEqual(grouped_by_partner[0][0].id, self.partner.id, "Grouped partner ID should match")

        # Group by product_id
        grouped_by_product = self.env['product.wishlist']._read_group(
            domain=[('id', '=', self.wishlist.id)],
            groupby=['product_id']
        )
        self.assertTrue(len(grouped_by_product) > 0, "Group by product should yield results")
        self.assertEqual(grouped_by_product[0][0].id, self.product.id, "Grouped product ID should match")

        _logger.info("Wishlist backend search and group by functionality validated successfully")
