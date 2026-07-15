# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install', 'theme_diva')
class TestProductFeaturedRelation(TransactionCase):
    """Tests for the product.featured.relation bridge model."""

    # ------------------------------------------------------------------
    # 1. Model & field presence
    # ------------------------------------------------------------------

    def test_field_product_id_exists(self):
        self.assertIn('product_id',
                      self.env['product.featured.relation']._fields)

    def test_field_featured_rel_id_exists(self):
        self.assertIn('featured_rel_id',
                      self.env['product.featured.relation']._fields)

    def test_field_product_id_comodel(self):
        field = self.env['product.featured.relation']._fields['product_id']
        self.assertEqual(field.type, 'many2one')
        self.assertEqual(field.comodel_name, 'product.template')

    def test_field_featured_rel_id_comodel(self):
        field = self.env['product.featured.relation']._fields['featured_rel_id']
        self.assertEqual(field.type, 'many2one')
        self.assertEqual(field.comodel_name, 'product.featured')

    # ------------------------------------------------------------------
    # 2. Record creation
    # ------------------------------------------------------------------

    def test_create_relation_record(self):
        """A product.featured.relation record must be creatable."""
        product = self.env['product.template'].create({
            'name': 'Relation Test Product',
            'type': 'service',
        })
        featured = self.env['product.featured'].create({'name': 'Rel Featured'})
        rel = self.env['product.featured.relation'].create({
            'product_id': product.id,
            'featured_rel_id': featured.id,
        })
        self.assertTrue(rel.exists())
        self.assertEqual(rel.product_id, product)
        self.assertEqual(rel.featured_rel_id, featured)


@tagged('post_install', '-at_install', 'theme_diva')
class TestWebsiteProductFeatured(TransactionCase):
    """Tests for the product.featured model."""

    # ------------------------------------------------------------------
    # 1. Model & field presence
    # ------------------------------------------------------------------

    def test_field_name_exists(self):
        self.assertIn('name', self.env['product.featured']._fields)

    def test_field_website_published_exists(self):
        self.assertIn('website_published', self.env['product.featured']._fields)

    def test_field_featured_list_ids_exists(self):
        self.assertIn('featured_list_ids', self.env['product.featured']._fields)

    def test_field_user_id_exists(self):
        self.assertIn('user_id', self.env['product.featured']._fields)

    def test_field_featured_list_ids_is_one2many(self):
        field = self.env['product.featured']._fields['featured_list_ids']
        self.assertEqual(field.type, 'one2many')
        self.assertEqual(field.comodel_name, 'product.featured.relation')

    def test_field_website_published_default_false(self):
        """website_published must default to False on new records."""
        featured = self.env['product.featured'].create({'name': 'Unpublished'})
        self.assertFalse(featured.website_published)

    def test_field_user_id_default_current_user(self):
        """user_id must default to the current user."""
        featured = self.env['product.featured'].create({'name': 'User Default'})
        self.assertEqual(featured.user_id, self.env.user)

    # ------------------------------------------------------------------
    # 2. _default_featured_list
    # ------------------------------------------------------------------

    def test_default_featured_list_populated(self):
        """_default_featured_list must populate featured_list_ids on creation."""
        # Ensure at least one published product exists
        self.env['product.template'].create([
            {'name': f'Default Product {i}', 'type': 'service'}
            for i in range(3)
        ])
        featured = self.env['product.featured'].create({'name': 'With Defaults'})
        self.assertTrue(len(featured.featured_list_ids) > 0)

    def test_default_featured_list_max_eight(self):
        """_default_featured_list must include at most 8 products."""
        # Create more than 8 products to test the limit
        self.env['product.template'].create([
            {'name': f'Overflow Product {i}', 'type': 'service'}
            for i in range(10)
        ])
        featured = self.env['product.featured'].create({'name': 'Max Eight'})
        self.assertLessEqual(len(featured.featured_list_ids), 8)

    def test_default_featured_list_links_product_templates(self):
        """Each item in featured_list_ids must link to a product.template.

        _default_featured_list fetches the first 8 products by default order
        (id asc). We verify the list contains valid product.template records
        from the existing catalogue rather than assuming a newly created product
        lands inside the top-8 window.
        """
        featured = self.env['product.featured'].create({'name': 'Link Check'})
        product_ids = featured.featured_list_ids.mapped('product_id')
        # Every entry must be a real, existing product.template
        self.assertTrue(product_ids, "featured_list_ids must not be empty")
        for product in product_ids:
            self.assertIn(
                'product.template',
                str(product),
                "Each relation must point to a product.template record",
            )
            self.assertTrue(product.exists(),
                            f"product.template({product.id}) must exist in DB")

    # ------------------------------------------------------------------
    # 3. Publishing behaviour
    # ------------------------------------------------------------------

    def test_publish_sets_website_published_true(self):
        """Setting website_published=True must persist on the record."""
        featured = self.env['product.featured'].create({'name': 'Publish Me'})
        featured.website_published = True
        featured.flush_recordset()
        self.assertTrue(featured.website_published)

    # ------------------------------------------------------------------
    # 4. featured_list_ids management
    # ------------------------------------------------------------------

    def test_add_product_to_featured_list(self):
        """Adding a product to featured_list_ids must be reflected on the record."""
        featured = self.env['product.featured'].create({
            'name': 'Manual Featured',
            'featured_list_ids': [],
        })
        product = self.env['product.template'].create({
            'name': 'Added Product',
            'type': 'service',
        })
        featured.write({
            'featured_list_ids': [(0, 0, {'product_id': product.id})]
        })
        self.assertIn(
            product,
            featured.featured_list_ids.mapped('product_id'),
        )

    def test_remove_product_from_featured_list(self):
        """Unlinking a relation record must remove it from featured_list_ids."""
        product = self.env['product.template'].create({
            'name': 'Remove Product',
            'type': 'service',
        })
        featured = self.env['product.featured'].create({
            'name': 'Remove Test',
            'featured_list_ids': [(0, 0, {'product_id': product.id})],
        })
        self.assertEqual(len(featured.featured_list_ids), 1)
        featured.featured_list_ids.unlink()
        featured.invalidate_recordset()
        self.assertEqual(len(featured.featured_list_ids), 0)

    def test_delete_featured_record(self):
        """A product.featured record must be deletable."""
        featured = self.env['product.featured'].create({'name': 'Delete Me'})
        feat_id = featured.id
        featured.unlink()
        self.assertFalse(
            self.env['product.featured'].browse(feat_id).exists()
        )

    # ------------------------------------------------------------------
    # 5. website.published.mixin presence
    # ------------------------------------------------------------------

    def test_inherits_website_published_mixin(self):
        """product.featured must expose website_url via website.published.mixin."""
        self.assertIn('website_url', self.env['product.featured']._fields)

    # ------------------------------------------------------------------
    # 6. mail.thread presence
    # ------------------------------------------------------------------

    def test_inherits_mail_thread(self):
        """product.featured must have message_ids from mail.thread."""
        self.assertIn('message_ids', self.env['product.featured']._fields)