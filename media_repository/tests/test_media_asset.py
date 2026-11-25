# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Muhammed Muflih c(odoo@cybrosys.com)
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
import base64
from unittest.mock import MagicMock, patch

from odoo import Command
from odoo.tests.common import Form, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMediaAsset(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env['media.category'].create({
            'name': 'Test Category',
        })
        cls.tag_1 = cls.env['media.tag'].create({
            'name': 'Test Tag 1',
        })
        cls.tag_2 = cls.env['media.tag'].create({
            'name': 'Test Tag 2',
        })
        # Exactly 1 MB (1,048,576 bytes) for deterministic file size assertions
        cls.sample_content = b'X' * (1024 * 1024)
        cls.sample_b64 = base64.b64encode(cls.sample_content)

    def test_01_create_media_asset_file(self):
        """Test creating a media asset with file upload, category and tags."""
        asset = self.env['media.asset'].create({
            'name': 'Test Image Asset',
            'description': 'A sample test image asset description.',
            'media_type': 'image',
            'source_type': 'file',
            'file': self.sample_b64,
            'file_name': 'test_image.png',
            'category_id': self.category.id,
            'media_tag_ids': [Command.set([self.tag_1.id, self.tag_2.id])],
            'favorite': True,
        })
        self.assertEqual(asset.name, 'Test Image Asset')
        self.assertEqual(asset.state, 'draft')
        self.assertEqual(asset.category_id, self.category)
        self.assertEqual(len(asset.media_tag_ids), 2)
        self.assertTrue(asset.favorite)
        self.assertEqual(asset.source_type, 'file')

        # Trigger file size computation and verify expected exact size in MB (1.0 MB)
        asset._compute_file_size()
        self.assertAlmostEqual(asset.file_size, 1.0, places=3)

    def test_02_create_media_asset_url(self):
        """Test creating media assets with URL source type and validating selection keys."""
        # Verify valid selections in the model definition
        media_type_keys = [k for k, _ in self.env['media.asset']._fields['media_type'].selection]
        source_type_keys = [k for k, _ in self.env['media.asset']._fields['source_type'].selection]

        self.assertIn('url', media_type_keys)
        self.assertIn('video', media_type_keys)
        self.assertIn('image', media_type_keys)
        self.assertIn('document', media_type_keys)
        self.assertIn('audio', media_type_keys)
        self.assertIn('url', source_type_keys)
        self.assertIn('file', source_type_keys)

        # 1. Asset with media_type='url' and source_type='url'
        asset_url = self.env['media.asset'].create({
            'name': 'External Link Asset',
            'media_type': 'url',
            'source_type': 'url',
            'source_url': 'https://www.example.com/article',
        })
        self.assertEqual(asset_url.media_type, 'url')
        self.assertEqual(asset_url.source_type, 'url')
        self.assertEqual(asset_url.source_url, 'https://www.example.com/article')
        asset_url._compute_file_size()
        self.assertEqual(asset_url.file_size, 0.0)

        # 2. Asset with media_type='video' and source_type='url' (external streaming video)
        asset_video_url = self.env['media.asset'].create({
            'name': 'Streaming Video Asset',
            'media_type': 'video',
            'source_type': 'url',
            'source_url': 'https://www.example.com/video.mp4',
        })
        self.assertEqual(asset_video_url.media_type, 'video')
        self.assertEqual(asset_video_url.source_type, 'url')
        self.assertEqual(asset_video_url.source_url, 'https://www.example.com/video.mp4')
        asset_video_url._compute_file_size()
        self.assertEqual(asset_video_url.file_size, 0.0)

    def test_03_confirm_asset(self):
        """Test confirming a media asset transitions from draft to confirmed."""
        asset = self.env['media.asset'].create({
            'name': 'Asset to Confirm',
            'media_type': 'document',
        })
        self.assertEqual(asset.state, 'draft')
        asset.action_confirm()
        self.assertEqual(asset.state, 'confirmed')

        # Calling action_confirm again on already confirmed asset should be a no-op
        asset.action_confirm()
        self.assertEqual(asset.state, 'confirmed')

        # Calling confirm() for backwards compatibility should also work
        asset_legacy = self.env['media.asset'].create({
            'name': 'Legacy Confirm Test',
            'media_type': 'document',
        })
        asset_legacy.confirm()
        self.assertEqual(asset_legacy.state, 'confirmed')

    def test_04_onchange_file(self):
        """Test onchange file behavior via browser Form simulation and direct call."""
        # 1. Simulate browser view onchange behavior using Form
        with Form(self.env['media.asset']) as asset_form:
            asset_form.name = 'Form Onchange Asset'
            asset_form.media_type = 'image'
            asset_form.source_type = 'file'
            asset_form.file = self.sample_b64
            asset_form.file_name = 'sample.png'

        asset = asset_form.record
        self.assertEqual(asset.file_name, 'sample.png')

        # Simulate clearing the file in the form (triggers @api.onchange('file'))
        with Form(asset) as edit_form:
            edit_form.file = False

        self.assertFalse(asset.file_name)
        self.assertEqual(asset.file_size, 0.0)

        # 2. Also verify direct method invocation with present and cleared file
        direct_asset = self.env['media.asset'].create({
            'name': 'Direct Onchange Test',
            'media_type': 'image',
            'file': self.sample_b64,
            'file_name': 'sample2.png',
        })
        direct_asset._onchange_file()
        self.assertEqual(direct_asset.file_name, 'sample2.png')

        direct_asset.file = False
        direct_asset._onchange_file()
        self.assertFalse(direct_asset.file_name)
        self.assertEqual(direct_asset.file_size, 0.0)

    def test_05_get_media_type_data(self):
        """Test dashboard get_media_type_data with exact count verification relative to baseline."""
        # Capture baseline counts before creating test assets to isolate from any existing DB records
        initial_data = self.env['media.asset'].get_media_type_data()
        self.assertIn('count', initial_data)
        self.assertIn('name', initial_data)
        self.assertEqual(initial_data['name'], ['Image', 'Video', 'Document', 'URL', 'Audio'])
        initial_counts = dict(zip(initial_data['name'], initial_data['count']))

        # Create known exact quantities: 2 images, 1 video, 1 doc, 1 url, 1 audio
        self.env['media.asset'].create([
            {'name': 'Img 1', 'media_type': 'image'},
            {'name': 'Img 2', 'media_type': 'image'},
            {'name': 'Vid 1', 'media_type': 'video'},
            {'name': 'Doc 1', 'media_type': 'document'},
            {'name': 'URL 1', 'media_type': 'url'},
            {'name': 'Aud 1', 'media_type': 'audio'},
        ])

        dashboard_data = self.env['media.asset'].get_media_type_data()
        current_counts = dict(zip(dashboard_data['name'], dashboard_data['count']))

        # Verify exact increment counts
        self.assertEqual(current_counts['Image'], initial_counts['Image'] + 2)
        self.assertEqual(current_counts['Video'], initial_counts['Video'] + 1)
        self.assertEqual(current_counts['Document'], initial_counts['Document'] + 1)
        self.assertEqual(current_counts['URL'], initial_counts['URL'] + 1)
        self.assertEqual(current_counts['Audio'], initial_counts['Audio'] + 1)

    def test_06_compute_file_size_attachment_edge_cases(self):
        """Test file size calculation edge cases isolating data without raw SQL updates."""
        asset = self.env['media.asset'].create({
            'name': 'Attachment Size Test Asset',
            'media_type': 'document',
            'source_type': 'file',
            'file': self.sample_b64,
        })
        # Standard compute from ORM-created attachment
        asset._compute_file_size()
        self.assertAlmostEqual(asset.file_size, 1.0, places=2)

        # Test the 2GB integer overflow edge case handled in _compute_file_size
        # using a clean mock without raw SQL DB mutation
        mock_attachment = MagicMock()
        mock_attachment.file_size = 2147483647
        mock_attachment.store_fname = 'dummy_store_fname'
        mock_attachment._full_path.return_value = '/dummy/path'

        with patch.object(self.env['ir.attachment'].__class__, 'search', return_value=mock_attachment):
            with patch('os.path.getsize', return_value=5 * 1024 * 1024 * 1024):  # 5 GB
                asset._compute_file_size()
                self.assertAlmostEqual(asset.file_size, 5120.0, places=1)

            # Test exception branch during os.path.getsize
            with patch('os.path.getsize', side_effect=OSError("Disk read error")):
                asset._compute_file_size()
                # Falls back safely to 2147483647 bytes (~2047.99 MB)
                self.assertAlmostEqual(asset.file_size, 2147483647 / (1024.0 * 1024.0), places=2)

        # Test case where record has no id yet or source_type != 'file'
        new_asset = self.env['media.asset'].new({'source_type': 'file'})
        new_asset._compute_file_size()
        self.assertEqual(new_asset.file_size, 0.0)

        url_asset = self.env['media.asset'].new({'source_type': 'url'})
        url_asset._compute_file_size()
        self.assertEqual(url_asset.file_size, 0.0)

    def test_07_media_category_and_tag_crud(self):
        """Test CRUD operations on media.category and media.tag."""
        self.assertTrue(self.env['media.category']._fields['name'].required)
        self.assertTrue(self.env['media.tag']._fields['name'].required)

        cat = self.env['media.category'].create({'name': 'Temporary Category'})
        self.assertEqual(cat.name, 'Temporary Category')
        cat.write({'name': 'Updated Category'})
        self.assertEqual(cat.name, 'Updated Category')
        self.assertTrue(cat.unlink())

        tag = self.env['media.tag'].create({'name': 'Temporary Tag'})
        self.assertEqual(tag.name, 'Temporary Tag')
        tag.write({'name': 'Updated Tag'})
        self.assertEqual(tag.name, 'Updated Tag')
        self.assertTrue(tag.unlink())
