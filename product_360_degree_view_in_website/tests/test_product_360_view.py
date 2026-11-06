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
import re
from psycopg2 import IntegrityError

from odoo.exceptions import AccessError
from odoo.tests import HttpCase, TransactionCase, tagged
from odoo.tests.common import new_test_user
from odoo.tools import mute_logger

# 1x1 PNG, used as the image of the 360° view lines
PNG_IMAGE = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQ'
    'GAhKmMIQAAAABJRU5ErkJggg=='
)


class Product360Common:
    """Shared helpers for the 360° view tests."""

    @classmethod
    def _create_template(cls, name='360 Product', is_360=True, images=3):
        """Create a published product template with `images` 360° lines."""
        template = cls.env['product.template'].create({
            'name': name,
            'is_boolean': is_360,
            'sale_ok': True,
            'website_published': True,
            'image_view_ids': [(0, 0, {
                'name': 'Angle %s' % index,
                'image_130': PNG_IMAGE,
            }) for index in range(images)],
        })
        return template


@tagged('post_install', '-at_install')
class TestProduct360Models(Product360Common, TransactionCase):

    def test_defaults(self):
        """The 360° view is disabled by default and has no images."""
        template = self.env['product.template'].create({'name': 'Plain'})
        self.assertFalse(template.is_boolean)
        self.assertFalse(template.image_view_ids)
        self.assertFalse(template.product_variant_id.is_boolean)
        self.assertFalse(template.product_variant_id.product_image_view_ids)

    def test_template_image_lines(self):
        """Image lines are linked to the product template."""
        template = self._create_template(images=4)
        self.assertTrue(template.is_boolean)
        self.assertEqual(len(template.image_view_ids), 4)
        self.assertEqual(
            template.image_view_ids.mapped('name'),
            ['Angle 0', 'Angle 1', 'Angle 2', 'Angle 3'])
        self.assertTrue(
            all(line.image_id == template
                for line in template.image_view_ids))

    def test_add_and_remove_template_line(self):
        """Lines can be added to and removed from an existing template."""
        template = self._create_template(images=1)
        template.write({'image_view_ids': [(0, 0, {
            'name': 'Extra', 'image_130': PNG_IMAGE})]})
        self.assertEqual(len(template.image_view_ids), 2)
        template.image_view_ids.filtered(
            lambda line: line.name == 'Extra').unlink()
        self.assertEqual(len(template.image_view_ids), 1)

    def test_product_variant_image_lines(self):
        """Image lines of a variant are stored on the variant only."""
        template = self._create_template(images=2)
        variant = template.product_variant_id
        variant.write({
            'is_boolean': True,
            'product_image_view_ids': [(0, 0, {
                'name': 'Variant angle',
                'image_130': PNG_IMAGE,
            })],
        })
        self.assertTrue(variant.is_boolean)
        self.assertEqual(len(variant.product_image_view_ids), 1)
        self.assertEqual(variant.product_image_view_ids.product_image_id,
                         variant)
        # the template lines are not touched by the variant lines
        self.assertEqual(len(template.image_view_ids), 2)

    def test_label_is_required(self):
        """A line without a label cannot be saved."""
        template = self._create_template(images=0)
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            self.env['image.view'].create({
                'image_130': PNG_IMAGE,
                'image_id': template.id,
            })

    def test_image_field_is_required(self):
        """The image is mandatory on the line (enforced by the form view,
        as attachment based images have no database column)."""
        self.assertTrue(self.env['image.view']._fields['image_130'].required)
        self.assertTrue(
            self.env['product.image.view']._fields['image_130'].required)

    def test_variant_line_requires_label(self):
        """The same label constraint applies to the variant lines."""
        variant = self._create_template(images=0).product_variant_id
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            self.env['product.image.view'].create({
                'image_130': PNG_IMAGE,
                'product_image_id': variant.id,
            })


@tagged('post_install', '-at_install')
class TestProduct360Security(Product360Common, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.template = cls._create_template(images=1)
        cls.variant = cls.template.product_variant_id
        cls.variant.product_image_view_ids = [(0, 0, {
            'name': 'Variant angle', 'image_130': PNG_IMAGE})]
        cls.internal_user = new_test_user(
            cls.env, login='product_360_internal', groups='base.group_user')
        cls.public_user = cls.env.ref('base.public_user')

    def test_internal_user_full_access(self):
        """Internal users can read, write, create and delete the lines."""
        line = self.template.image_view_ids.with_user(self.internal_user)
        self.assertEqual(line.name, 'Angle 0')
        line.write({'name': 'Renamed'})
        self.assertEqual(line.name, 'Renamed')
        new_line = self.env['image.view'].with_user(
            self.internal_user).create({
            'name': 'New',
            'image_130': PNG_IMAGE,
            'image_id': self.template.id,
        })
        new_line.unlink()

    def test_public_user_read_only(self):
        """The public user can only read the lines, not change them."""
        for lines in (self.template.image_view_ids,
                      self.variant.product_image_view_ids):
            line = lines.with_user(self.public_user)
            self.assertTrue(line.read(['name']))
            with self.assertRaises(AccessError):
                line.write({'name': 'Hacked'})
            with self.assertRaises(AccessError):
                line.unlink()
        with self.assertRaises(AccessError):
            self.env['image.view'].with_user(self.public_user).create({
                'name': 'Hacked',
                'image_130': PNG_IMAGE,
                'image_id': self.template.id,
            })
        with self.assertRaises(AccessError):
            self.env['product.image.view'].with_user(self.public_user).create({
                'name': 'Hacked',
                'image_130': PNG_IMAGE,
                'product_image_id': self.variant.id,
            })


@tagged('post_install', '-at_install')
class TestProduct360Website(Product360Common, HttpCase):

    def test_360_block_is_shown(self):
        """The product page shows the 360° block and one frame per image."""
        template = self._create_template(images=3)
        response = self.url_open(template.website_url)
        self.assertEqual(response.status_code, 200)
        html = response.text
        self.assertIn('id="image_360"', html)
        self.assertIn('view_360', html)
        self.assertIn('stop_view', html)
        for line in template.image_view_ids:
            self.assertIn(
                '/web/image/image.view/%s/image_130/1024x1024' % line.id,
                html)
        block = html.split('id="image_360"', 1)[1]
        self.assertEqual(len(re.findall(r'<li\b', block.split('</ul>')[0])), 3)

    def test_360_block_is_hidden_when_disabled(self):
        """Without the checkbox the page has no 360° block."""
        template = self._create_template(
            name='Normal Product', is_360=False, images=2)
        response = self.url_open(template.website_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('id="image_360"', response.text)
        self.assertNotIn('view_360', response.text)

    def test_public_can_load_360_image(self):
        """The public visitor can load the 360° images."""
        template = self._create_template(images=1)
        line = template.image_view_ids
        response = self.url_open(
            '/web/image/image.view/%s/image_130/1024x1024' % line.id)
        self.assertEqual(response.status_code, 200)
