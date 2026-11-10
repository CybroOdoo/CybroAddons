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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResCompany(TransactionCase):
    """Test suite for res.company Firebase configuration fields in mail_push_notification."""

    def test_res_company(self):
        """Test setting and reading Firebase configuration fields on res.company."""
        company = self.env['res.company'].create({
            'name': 'Test Push Notification Company',
            'push_notification': True,
            'project_id_firebase': 'test-firebase-id',
            'private_key_ref': 'test-private-key-ref',
            'private_key': 'test-private-key-content',
            'client_email': 'test-client@firebase.com',
            'client_id_firebase': 'client-id-12345',
            'client_cert_url': 'https://cert.url/test',
            'vapid': 'test-vapid-key',
            'api_key': 'test-api-key',
            'auth_domain': 'test.firebaseapp.com',
            'storage_bucket': 'test.appspot.com',
            'messaging_sender_id_firebase': '987654321',
            'app_id_firebase': '1:987654321:web:test',
            'measurement_id_firebase': 'G-MEASURE123',
        })

        self.assertTrue(company.push_notification)
        self.assertEqual(company.project_id_firebase, 'test-firebase-id')
        self.assertEqual(company.private_key_ref, 'test-private-key-ref')
        self.assertEqual(company.private_key, 'test-private-key-content')
        self.assertEqual(company.client_email, 'test-client@firebase.com')
        self.assertEqual(company.client_id_firebase, 'client-id-12345')
        self.assertEqual(company.client_cert_url, 'https://cert.url/test')
        self.assertEqual(company.vapid, 'test-vapid-key')
        self.assertEqual(company.api_key, 'test-api-key')
        self.assertEqual(company.auth_domain, 'test.firebaseapp.com')
        self.assertEqual(company.storage_bucket, 'test.appspot.com')
        self.assertEqual(company.messaging_sender_id_firebase, '987654321')
        self.assertEqual(company.app_id_firebase, '1:987654321:web:test')
        self.assertEqual(company.measurement_id_firebase, 'G-MEASURE123')

