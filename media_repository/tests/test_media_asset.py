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
#############################################################################
import base64

from odoo import Command, fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMediaAsset(TransactionCase):
    """Automated unit test suite for the Media Repository module, ensuring
    comprehensive coverage (>= 80%) across media assets, categories, tags,
    state transitions, computed fields, onchanges, and multi-recordset actions.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.base_user_group = cls.env.ref('base.group_user')
        cls.user_group = cls.env.ref('media_repository.group_user')
        cls.manager_group = cls.env.ref('media_repository.group_manager')

        # Test users
        cls.media_user = cls.env['res.users'].create({
            'name': 'Media Standard User',
            'login': 'media_user_test',
            'email': 'media_user@example.com',
            'group_ids': [
                Command.link(cls.base_user_group.id),
                Command.link(cls.user_group.id),
            ],
        })
        cls.media_manager = cls.env['res.users'].create({
            'name': 'Media Manager User',
            'login': 'media_manager_test',
            'email': 'media_manager@example.com',
            'group_ids': [
                Command.link(cls.base_user_group.id),
                Command.link(cls.manager_group.id),
            ],
        })

        # Test category and tags
        cls.category_images = cls.env['media.category'].create({
            'name': 'Brand Graphics',
        })
        cls.category_docs = cls.env['media.category'].create({
            'name': 'Official Documents',
        })
        cls.tag_promo = cls.env['media.tag'].create({
            'name': 'Promotional',
        })
        cls.tag_internal = cls.env['media.tag'].create({
            'name': 'Internal Only',
        })

        # Sample binary content
        cls.sample_content = base64.b64encode(b"Dummy media content for testing").decode('ascii')

    def test_01_media_category_and_tag_crud(self):
        """Test basic creation and attributes of categories and tags."""
        category = self.env['media.category'].create({'name': 'Tutorial Videos'})
        self.assertEqual(category.name, 'Tutorial Videos')
        category.write({'name': 'Instructional Videos'})
        self.assertEqual(category.name, 'Instructional Videos')

        tag = self.env['media.tag'].create({'name': 'High Priority'})
        self.assertEqual(tag.name, 'High Priority')
        tag.write({'name': 'Urgent'})
        self.assertEqual(tag.name, 'Urgent')

    def test_02_create_file_asset_defaults(self):
        """Test creation of a media asset with default values and file source."""
        asset = self.env['media.asset'].create({
            'name': 'Company Logo',
            'media_type': 'image',
            'source_type': 'file',
            'category_id': self.category_images.id,
            'media_tag_ids': [Command.link(self.tag_promo.id)],
            'description': 'Main official corporate logo in PNG format.',
        })
        self.assertEqual(asset.state, 'draft')
        self.assertFalse(asset.favorite)
        self.assertEqual(asset.create_uid, self.env.user)
        self.assertEqual(asset.create_date.date(), fields.Date.today())
        self.assertEqual(asset.category_id, self.category_images)
        self.assertIn(self.tag_promo, asset.media_tag_ids)

    def test_03_create_url_asset(self):
        """Test creation of URL-based media asset."""
        asset = self.env['media.asset'].create({
            'name': 'Promo Video Link',
            'media_type': 'url',
            'source_type': 'url',
            'source_url': 'https://www.example.com/videos/promo',
            'favorite': True,
        })
        self.assertEqual(asset.media_type, 'url')
        self.assertEqual(asset.source_type, 'url')
        self.assertEqual(asset.source_url, 'https://www.example.com/videos/promo')
        self.assertTrue(asset.favorite)
        self.assertEqual(asset.file_size, 0.0)

    def test_04_compute_file_size_with_attachment(self):
        """Test _compute_file_size when ir.attachment exists and when it does not."""
        raw_bytes = b"Hello World Antigravity Odoo Media Test" * 1000
        encoded_content = base64.b64encode(raw_bytes).decode('ascii')
        asset = self.env['media.asset'].create({
            'name': 'Whitepaper PDF',
            'media_type': 'document',
            'source_type': 'file',
            'file': encoded_content,
            'file_name': 'whitepaper.pdf',
        })

        # Create or update corresponding ir.attachment record
        attachment = self.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'media.asset'),
            ('res_field', '=', 'file'),
            ('res_id', '=', asset.id),
        ], limit=1)
        if not attachment:
            attachment = self.env['ir.attachment'].sudo().create({
                'name': 'whitepaper.pdf',
                'res_model': 'media.asset',
                'res_field': 'file',
                'res_id': asset.id,
                'raw': raw_bytes,
            })
        else:
            attachment.write({'raw': raw_bytes})

        asset._compute_file_size()
        expected_mb = len(raw_bytes) / (1024.0 * 1024.0)
        self.assertAlmostEqual(asset.file_size, expected_mb, places=3)

        # Non-file source should compute to 0.0
        asset.write({'source_type': 'url'})
        asset._compute_file_size()
        self.assertEqual(asset.file_size, 0.0)

    def test_05_onchange_file(self):
        """Test _onchange_file resets file_name and file_size when file is cleared."""
        asset = self.env['media.asset'].new({
            'name': 'Brochure Draft',
            'media_type': 'document',
            'source_type': 'file',
            'file': self.sample_content,
            'file_name': 'brochure.pdf',
            'file_size': 1.5,
        })
        # Simulate clearing the file field in UI
        asset.file = False
        asset._onchange_file()
        self.assertFalse(asset.file_name)
        self.assertEqual(asset.file_size, 0.0)

    def test_06_confirm_single_and_multi_recordset(self):
        """Test single and multi-recordset confirmation action."""
        asset_1 = self.env['media.asset'].create({
            'name': 'Asset One',
            'media_type': 'image',
            'state': 'draft',
        })
        asset_2 = self.env['media.asset'].create({
            'name': 'Asset Two',
            'media_type': 'video',
            'state': 'draft',
        })

        # Single record confirm
        asset_1.confirm()
        self.assertEqual(asset_1.state, 'confirmed')

        # Re-confirming an already confirmed record should not alter state
        asset_1.confirm()
        self.assertEqual(asset_1.state, 'confirmed')

        # Multi-recordset confirm
        asset_3 = self.env['media.asset'].create({
            'name': 'Asset Three',
            'media_type': 'document',
            'state': 'draft',
        })
        combined = asset_2 | asset_3
        combined.confirm()
        self.assertEqual(asset_2.state, 'confirmed')
        self.assertEqual(asset_3.state, 'confirmed')

    def test_07_get_media_type_data(self):
        """Test get_media_type_data dashboard data aggregation."""
        # Clean existing assets to get deterministic counts
        self.env['media.asset'].search([]).unlink()

        # Create assets across all types
        self.env['media.asset'].create([
            {'name': 'Img 1', 'media_type': 'image'},
            {'name': 'Img 2', 'media_type': 'image'},
            {'name': 'Vid 1', 'media_type': 'video'},
            {'name': 'Doc 1', 'media_type': 'document'},
            {'name': 'Url 1', 'media_type': 'url'},
            {'name': 'Aud 1', 'media_type': 'audio'},
            {'name': 'Aud 2', 'media_type': 'audio'},
            {'name': 'Aud 3', 'media_type': 'audio'},
        ])

        data = self.env['media.asset'].get_media_type_data()
        self.assertIn('count', data)
        self.assertIn('name', data)
        self.assertEqual(data['name'], ['Image', 'Video', 'Document', 'Url', 'Audio'])
        # [image, video, document, url, audio]
        self.assertEqual(data['count'], [2, 1, 1, 1, 3])

    def test_08_media_asset_access_rules(self):
        """Test user and manager access control rules."""
        # Regular user can create and read their own asset
        user_asset = self.env['media.asset'].with_user(self.media_user).create({
            'name': 'User Personal Image',
            'media_type': 'image',
            'source_type': 'file',
        })
        self.assertEqual(user_asset.create_uid, self.media_user)

        # Manager can read and edit any asset
        manager_asset_view = user_asset.with_user(self.media_manager)
        manager_asset_view.write({'name': 'Manager Updated Title'})
        self.assertEqual(user_asset.name, 'Manager Updated Title')

        # Manager can unlink assets
        manager_asset_view.unlink()
        self.assertFalse(user_asset.exists())

