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
#############################################################################
import io
import zipfile

from odoo.tests.common import HttpCase, tagged


@tagged('-at_install', 'post_install')
class TestChatterAttachmentAsZip(HttpCase):
    """
    HTTP test case for DownloadAllAttachments controller functions and routes.
    Tests /chatter/attachments/download/zip and /chatter/attach_load/zip endpoints.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner HTTP',
            'email': 'test_partner_http@example.com',
        })
        cls.partner_empty = cls.env['res.partner'].create({
            'name': 'Test Partner HTTP Empty',
            'email': 'test_partner_http_empty@example.com',
        })
        cls.attachment_1 = cls.env['ir.attachment'].create({
            'name': 'invoice.pdf',
            'raw': b'%PDF-1.4 test http content 1',
            'res_model': 'res.partner',
            'res_id': cls.partner.id,
            'mimetype': 'application/pdf',
        })
        cls.attachment_2 = cls.env['ir.attachment'].create({
            'name': 'photo.png',
            'raw': b'\x89PNG\r\n\x1a\n test png content',
            'res_model': 'res.partner',
            'res_id': cls.partner.id,
            'mimetype': 'image/png',
        })
        cls.admin_user = cls.env.ref('base.user_admin')

    def test_download_attachments(self):
        """
        Test the HTTP GET request to /chatter/attachments/download/zip
        with an authenticated user, verifying response code, headers, and zip content.
        """
        self.authenticate(self.admin_user.login, self.admin_user.login)
        url = f'/chatter/attachments/download/zip?res_id={self.partner.id}&res_model=res.partner'
        response = self.url_open(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('Content-Type'), 'application/zip')
        expected_filename = f'attachments_res.partner_{self.partner.id}.zip'
        self.assertEqual(
            response.headers.get('Content-Disposition'),
            f'attachment; filename="{expected_filename}"'
        )

        # Verify zip content
        with zipfile.ZipFile(io.BytesIO(response.content), 'r') as zipf:
            filenames = zipf.namelist()
            self.assertIn('invoice.pdf', filenames)
            self.assertIn('photo.png', filenames)
            self.assertEqual(zipf.read('invoice.pdf'), b'%PDF-1.4 test http content 1')
            self.assertEqual(zipf.read('photo.png'), b'\x89PNG\r\n\x1a\n test png content')

    def test_download_attachments_alternative_route(self):
        """
        Test the second route /chatter/attach_load/zip defined on the controller.
        """
        self.authenticate(self.admin_user.login, self.admin_user.login)
        url = f'/chatter/attach_load/zip?res_id={self.partner.id}&res_model=res.partner'
        response = self.url_open(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('Content-Type'), 'application/zip')
        expected_filename = f'attachments_res.partner_{self.partner.id}.zip'
        self.assertEqual(
            response.headers.get('Content-Disposition'),
            f'attachment; filename="{expected_filename}"'
        )
        with zipfile.ZipFile(io.BytesIO(response.content), 'r') as zipf:
            self.assertIn('invoice.pdf', zipf.namelist())

    def test_download_attachments_no_res_id(self):
        """
        Test HTTP GET request without res_id parameter.
        Should return an empty response with Content-Type application/zip.
        """
        self.authenticate(self.admin_user.login, self.admin_user.login)
        url = '/chatter/attachments/download/zip?res_model=res.partner'
        response = self.url_open(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'')
        self.assertEqual(response.headers.get('Content-Type'), 'application/zip')
        self.assertNotIn('Content-Disposition', response.headers)

    def test_download_attachments_invalid_res_id(self):
        """
        Test HTTP GET request with non-integer res_id.
        Should return an empty response with Content-Type application/zip.
        """
        self.authenticate(self.admin_user.login, self.admin_user.login)
        url = '/chatter/attachments/download/zip?res_id=not_an_integer&res_model=res.partner'
        response = self.url_open(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'')
        self.assertEqual(response.headers.get('Content-Type'), 'application/zip')

    def test_download_attachments_no_attachments(self):
        """
        Test HTTP GET request when record has no attachments.
        Should return an empty response with Content-Type application/zip.
        """
        self.authenticate(self.admin_user.login, self.admin_user.login)
        url = f'/chatter/attachments/download/zip?res_id={self.partner_empty.id}&res_model=res.partner'
        response = self.url_open(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'')
        self.assertEqual(response.headers.get('Content-Type'), 'application/zip')

    def test_download_attachments_without_res_model(self):
        """
        Test HTTP GET request omitting res_model parameter.
        Filename should use 'chatter' as default and include general attachments.
        """
        self.authenticate(self.admin_user.login, self.admin_user.login)
        url = f'/chatter/attachments/download/zip?res_id={self.partner.id}'
        response = self.url_open(url)

        self.assertEqual(response.status_code, 200)
        expected_filename = f'attachments_chatter_{self.partner.id}.zip'
        self.assertEqual(
            response.headers.get('Content-Disposition'),
            f'attachment; filename="{expected_filename}"'
        )
        with zipfile.ZipFile(io.BytesIO(response.content), 'r') as zipf:
            self.assertIn('invoice.pdf', zipf.namelist())

    def test_download_attachments_exclude_account_move(self):
        """
        Test that when res_model is not specified, attachments belonging
        to 'account.move' are excluded from the zip archive.
        """
        self.authenticate(self.admin_user.login, self.admin_user.login)
        # Create an attachment with res_model='account.move' and same res_id
        self.env['ir.attachment'].create({
            'name': 'account_move_doc.txt',
            'raw': b'Invoice details content',
            'res_model': 'account.move',
            'res_id': self.partner.id,
        })

        url = f'/chatter/attachments/download/zip?res_id={self.partner.id}'
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(response.content), 'r') as zipf:
            filenames = zipf.namelist()
            self.assertIn('invoice.pdf', filenames)
            self.assertNotIn('account_move_doc.txt', filenames)

    def test_download_attachments_unauthenticated(self):
        """
        Test accessing the download endpoint without authentication (auth='user').
        Should redirect to login page.
        """
        url = f'/chatter/attachments/download/zip?res_id={self.partner.id}&res_model=res.partner'
        response = self.url_open(url)
        # Should redirect to web/login or return 302/303 or login page content
        self.assertTrue(
            response.status_code in (302, 303, 401, 403) or
            '/web/login' in response.url or
            b'login' in response.content.lower()
        )

    def test_download_attachments_raw_content_variations(self):
        """
        Test handling of different attachment content types.
        """
        self.authenticate(self.admin_user.login, self.admin_user.login)
        partner_custom = self.env['res.partner'].create({
            'name': 'Custom Attachment Partner HTTP',
        })
        self.env['ir.attachment'].create({
            'name': 'sample_document.txt',
            'raw': b'Sample document content for download',
            'res_model': 'res.partner',
            'res_id': partner_custom.id,
        })

        url = f'/chatter/attachments/download/zip?res_id={partner_custom.id}&res_model=res.partner'
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(response.content), 'r') as zipf:
            filenames = zipf.namelist()
            self.assertIn('sample_document.txt', filenames)
            self.assertEqual(zipf.read('sample_document.txt'), b'Sample document content for download')
