# -*- coding: utf-8 -*-

import base64
from odoo.tests.common import HttpCase, tagged

@tagged('-at_install', 'post_install')
class TestMediaUploadController(HttpCase):

    def setUp(self):
        super().setUp()
        
        # Mock requests.get to bypass export_delete_login_log module making external IP API requests
        import requests
        from unittest.mock import patch, MagicMock
        mock_response = MagicMock()
        mock_response.json.return_value = {'ip': '127.0.0.1'}
        mock_response.status_code = 200
        patcher = patch.object(requests, 'get', return_value=mock_response)
        patcher.start()
        self.addCleanup(patcher.stop)
        
        self.MediaAsset = self.env['media.asset']
        
        # Ensure we have an admin user that can upload files
        with self.registry.cursor() as cr:
            env = self.env(cr=cr)
            admin = env.ref('base.user_admin')
            admin.write({'password': 'admin'})
            login = admin.login
            asset = env['media.asset'].create({
                'name': 'Controller Upload Test',
                'media_type': 'document',
                'source_type': 'file',
            })
            self.asset_id = asset.id
            cr.commit()
            
        self.asset = self.MediaAsset.browse(self.asset_id)
        self.authenticate(login, 'admin')

    def test_upload_media_asset_file(self):
        """Test the upload controller directly"""
        from odoo.http import Request
        file_content = b'test upload content'
        files = {
            'ufile': ('test_upload.txt', file_content, 'text/plain')
        }
        data = {
            'model': 'media.asset',
            'id': str(self.asset.id),
            'csrf_token': Request.csrf_token(self),
        }
        
        response = self.url_open(
            '/media_repository/asset/upload_file', 
            data=data, 
            files=files
        )
        self.assertEqual(response.status_code, 200)
        
        # Check response body
        result = response.json()
        self.assertEqual(result.get('file_name'), 'test_upload.txt')
        
        # Verify the file was attached and asset was updated
        self.asset.invalidate_recordset(['file_name', 'file_size', 'file'])
        self.assertEqual(self.asset.file_name, 'test_upload.txt')
        self.assertTrue(self.asset.file)
        self.assertEqual(base64.b64decode(self.asset.file), file_content)
        
    def test_upload_invalid_model(self):
        """Test upload controller with an invalid model"""
        from odoo.http import Request
        response = self.url_open(
            '/media_repository/asset/upload_file', 
            data={
                'model': 'invalid.model', 
                'id': str(self.asset.id),
                'csrf_token': Request.csrf_token(self),
            },
            files={'ufile': ('test.txt', b'content')}
        )
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertIn('error', result)
        self.assertEqual(result['error'], "Invalid model.")
