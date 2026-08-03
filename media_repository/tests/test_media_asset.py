# -*- coding: utf-8 -*-
import base64
from odoo.tests.common import TransactionCase

class TestMediaAsset(TransactionCase):

    def setUp(self):
        super(TestMediaAsset, self).setUp()
        self.MediaAsset = self.env['media.asset']
        self.Category = self.env['media.category'].create({'name': 'Images'})
        self.Tag = self.env['media.tag'].create({'name': 'Nature'})
        
        self.asset_data = {
            'name': 'Test Image',
            'media_type': 'image',
            'source_type': 'file',
            'category_id': self.Category.id,
            'media_tag_ids': [(6, 0, [self.Tag.id])],
        }

    def test_create_asset(self):
        """Test basic creation and fields of Media Asset"""
        asset = self.MediaAsset.create(self.asset_data)
        self.assertEqual(asset.state, 'draft')
        self.assertEqual(asset.name, 'Test Image')
        self.assertEqual(asset.media_type, 'image')
        self.assertEqual(asset.category_id, self.Category)
        self.assertIn(self.Tag, asset.media_tag_ids)
        
    def test_confirm_asset(self):
        """Test confirming a media asset"""
        asset = self.MediaAsset.create(self.asset_data)
        asset.confirm()
        self.assertEqual(asset.state, 'confirmed')

    def test_get_media_type_data(self):
        """Test fetching media type statistics"""
        self.MediaAsset.create({
            'name': 'Test Image',
            'media_type': 'image',
            'source_type': 'url',
            'source_url': 'http://example.com/image.jpg',
        })
        self.MediaAsset.create({
            'name': 'Test Video',
            'media_type': 'video',
            'source_type': 'url',
            'source_url': 'http://example.com/video.mp4',
        })
        
        data = self.MediaAsset.get_media_type_data()
        self.assertIn('count', data)
        self.assertIn('name', data)
        self.assertEqual(data['name'], ['Image', 'Video', 'Document', 'Url', 'Audio'])
        
        image_index = data['name'].index('Image')
        video_index = data['name'].index('Video')
        
        self.assertTrue(data['count'][image_index] >= 1)
        self.assertTrue(data['count'][video_index] >= 1)

    def test_file_size_computation(self):
        """Test that file size is correctly computed for file assets"""
        file_content = b"a" * (1024 * 1024)
        
        asset = self.MediaAsset.create({
            'name': 'Test Document',
            'media_type': 'document',
            'source_type': 'file',
            'file': base64.b64encode(file_content),
        })
        self.env.flush_all()
        
        self.assertAlmostEqual(asset.file_size, 1.0, places=5)
        
    def test_file_size_url_source(self):
        """Test that file size is 0 for URL source assets"""
        asset = self.MediaAsset.create({
            'name': 'Test URL',
            'media_type': 'url',
            'source_type': 'url',
            'source_url': 'http://example.com',
        })
        asset._compute_file_size()
        self.assertEqual(asset.file_size, 0.0)

    def test_onchange_file(self):
        """Test that file name and size reset when file is removed"""
        asset = self.MediaAsset.new(self.asset_data)
        asset.file = base64.b64encode(b"dummy")
        asset.file_name = "dummy.txt"
        asset.file_size = 1.0
        
        # Simulate clearing the file
        asset.file = False
        asset._onchange_file()
        
        self.assertFalse(asset.file_name)
        self.assertEqual(asset.file_size, 0.0)
