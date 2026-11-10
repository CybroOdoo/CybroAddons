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
import json

from odoo.exceptions import ValidationError
from odoo.tests.common import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestWebsiteSignupApproval(TransactionCase):
    """Test suite for Website Signup Approval module"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.doc_attachment_1 = cls.env['document.attachment'].create({
            'document': 'ID Proof',
        })
        cls.doc_attachment_2 = cls.env['document.attachment'].create({
            'document': 'Address Proof',
        })
        cls.config_param = cls.env['ir.config_parameter'].sudo()

    def test_01_document_attachment_creation(self):
        """Test document.attachment model creation and rec_name"""
        self.assertEqual(
            self.doc_attachment_1.document, 'ID Proof')
        self.assertEqual(
            self.doc_attachment_1.display_name, 'ID Proof')

    def test_02_res_config_settings(self):
        """Test setting and getting values in res.config.settings"""
        settings = self.env['res.config.settings'].create({
            'auth_signup_approval': True,
            'documents_ids': [
                (6, 0, [self.doc_attachment_1.id, self.doc_attachment_2.id]),
            ],
        })
        settings.set_values()
        self.assertTrue(
            self.config_param.get_bool(
                'website_signup_approval.auth_signup_approval'))
        stored_docs = json.loads(
            self.config_param.get_str(
                'website_signup_approval.documents_ids'))
        self.assertIn(self.doc_attachment_1.id, stored_docs)
        self.assertIn(self.doc_attachment_2.id, stored_docs)

        # Retrieve values via get_values
        values = settings.get_values()
        self.assertTrue(values.get('documents_ids'))
        self.assertEqual(
            set(values['documents_ids'][0][2]),
            {self.doc_attachment_1.id, self.doc_attachment_2.id})

    def test_03_approval_request_flow(self):
        """Test creation, approval, and rejection of signup requests"""
        test_email = 'applicant_test@example.com'
        test_password = 'SecretPassword123!'
        # Use sudo() as the password field is restricted to base.group_system
        approval = self.env['res.users.approve'].sudo().create({
            'name': 'Applicant Test',
            'email': test_email,
            'password': test_password,
            'attachment_ids': [(0, 0, {
                'attachments': 'dGVzdF9kYXRh',
            })],
        })
        self.assertFalse(approval.for_approval_menu)
        self.assertFalse(approval.hide_button)
        self.assertTrue(approval.sudo().password)
        self.assertEqual(len(approval.attachment_ids), 1)

        # Approve the request
        approval.action_approve_login()
        self.assertTrue(approval.for_approval_menu)
        self.assertTrue(approval.hide_button)
        self.assertTrue(approval.approved_date)
        # Password should be cleared from approval record after user creation
        self.assertFalse(approval.sudo().password)

        created_user = self.env['res.users'].sudo().search(
            [('login', '=', test_email)], limit=1)
        self.assertTrue(created_user)
        self.assertEqual(created_user.name, 'Applicant Test')
        portal_group = self.env.ref('base.group_portal')
        self.assertIn(portal_group, created_user.group_ids)

        # Verify authentication succeeds with the approved password
        auth_info = self.env['res.users'].authenticate(
            {'type': 'password', 'login': test_email,
             'password': test_password},
            {'interactive': False}
        )
        self.assertEqual(auth_info['uid'], created_user.id)

        # Reject the request
        approval.action_reject_login()
        self.assertFalse(approval.for_approval_menu)
        self.assertTrue(approval.hide_button)
        self.assertFalse(approval.approved_date)
        user_after_reject = self.env['res.users'].sudo().search(
            [('login', '=', test_email)], limit=1)
        self.assertFalse(user_after_reject)

    def test_04_multi_record_approval_rejection(self):
        """Test action_approve_login and action_reject_login on recordsets"""
        emails = ['multi1@example.com', 'multi2@example.com']
        records = self.env['res.users.approve'].create([
            {'name': 'User 1', 'email': emails[0]},
            {'name': 'User 2', 'email': emails[1]},
        ])
        # Approve both records simultaneously
        records.action_approve_login()
        for rec in records:
            self.assertTrue(rec.for_approval_menu)
            self.assertTrue(rec.hide_button)
            user = self.env['res.users'].sudo().search(
                [('login', '=', rec.email)], limit=1)
            self.assertTrue(user)

        # Reject both records simultaneously
        records.action_reject_login()
        for rec in records:
            self.assertFalse(rec.for_approval_menu)
            self.assertTrue(rec.hide_button)
            user = self.env['res.users'].sudo().search(
                [('login', '=', rec.email)], limit=1)
            self.assertFalse(user)

    def test_05_duplicate_email_prevention(self):
        """Test duplicate approval requests with same email are blocked"""
        test_email = 'unique_applicant@example.com'
        self.env['res.users.approve'].create({
            'name': 'Applicant First',
            'email': test_email,
        })
        with self.assertRaises(ValidationError):
            self.env['res.users.approve'].create({
                'name': 'Applicant Duplicate',
                'email': test_email,
            })

    def test_10_non_system_approver_can_approve_and_reject(self):
        """Approver with only Signup Approval User group must not raise AccessError.

        Regression guard for the 4.2 blocker: the password field is restricted
        to base.group_system, so users holding only the custom approval group
        would receive an AccessError if action_approve_login or
        action_reject_login tried to read/write it without sudo.
        """
        approval_group = self.env.ref(
            'website_signup_approval'
            '.website_signup_approval_group_approval_user')
        # Create a minimal internal user that belongs only to the approval group
        approver = self.env['res.users'].sudo().create({
            'name': 'Non-Admin Approver',
            'login': 'non_admin_approver@example.com',
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                approval_group.id,
            ])],
        })
        self.assertFalse(approver.has_group('base.group_system'))
        self.assertTrue(approver.has_group(
            'website_signup_approval.website_signup_approval_group_approval_user'))

        test_email = 'pending_user_non_admin@example.com'
        # Create the approval request as superuser (password field has groups=base.group_system)
        approval = self.env['res.users.approve'].sudo().create({
            'name': 'Pending User',
            'email': test_email,
            'password': 'TestPass123!',
        })
        # Switch context to the non-admin approver and call approve —
        # must not raise AccessError even though password has groups=base.group_system
        approval_as_approver = approval.with_user(approver)
        approval_as_approver.action_approve_login()
        self.assertTrue(approval.for_approval_menu)
        created = self.env['res.users'].sudo().search(
            [('login', '=', test_email)], limit=1)
        self.assertTrue(created)

        # Reject as the same non-admin approver
        approval_as_approver.action_reject_login()
        self.assertFalse(approval.for_approval_menu)
        deleted = self.env['res.users'].sudo().search(
            [('login', '=', test_email)], limit=1)
        self.assertFalse(deleted)


@tagged('post_install', '-at_install')
class TestWebsiteSignupApprovalHttp(HttpCase):
    """HTTP test suite for signup approval endpoints and login blocking"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config_param = cls.env['ir.config_parameter'].sudo()

    def setUp(self):
        super().setUp()
        self.config_param.set_bool(
            'website_signup_approval.auth_signup_approval', True)
        self.config_param.set_str(
            'auth_signup.invitation_scope', 'b2c')
        self.env['website'].search([]).write(
            {'auth_signup_uninvited': 'b2c'})

    def test_06_http_signup_b2b_public_access_blocked(self):
        """When invitation scope is b2b, public /web/signup must return 404"""
        self.config_param.set_str('auth_signup.invitation_scope', 'b2b')
        self.env['website'].search([]).write(
            {'auth_signup_uninvited': 'b2b'})
        res = self.url_open('/web/signup')
        self.assertEqual(res.status_code, 404)

    def test_07_http_signup_invitation_token_bypass(self):
        """When signup has a valid token, approval flow is bypassed"""
        partner = self.env['res.partner'].create({
            'name': 'Invited Partner',
            'email': 'invited_partner@example.com',
        })
        partner.signup_prepare()
        token = partner.sudo()._generate_signup_token()
        res = self.url_open(f'/web/signup?token={token}')
        self.assertEqual(res.status_code, 200)
        self.assertNotIn('is_signup_approval', res.text)

    def test_08_http_login_blocked_before_approval(self):
        """Login attempt is blocked with approval notice before approval"""
        test_email = 'pending_applicant@example.com'
        test_pass = 'SecretPass123!'
        # Use sudo() to write password field (guarded by base.group_system)
        self.env['res.users.approve'].sudo().create({
            'name': 'Pending Applicant',
            'email': test_email,
            'password': test_pass,
        })
        self.authenticate(None, None)
        res = self.url_open('/web/login', data={
            'login': test_email,
            'password': test_pass,
            'csrf_token': self.csrf_token(),
        })
        self.assertIn(
            'You can log in only after your account has been approved.',
            res.text)

    def test_09_rpc_create_attachment_endpoint(self):
        """POST to /web/signup/approve creates an approval request via RPC"""
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'id': 1,
            'params': {
                'username': 'RPC Applicant',
                'email': 'rpc_applicant@example.com',
                'password': 'RpcPass123!',
                'confirm_password': 'RpcPass123!',
                'data': [],
            },
        }
        res = self.url_open(
            '/web/signup/approve',
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn('result', body, body)
        result = body['result']
        self.assertTrue(
            result.get('success'),
            f"Expected success=True but got: {result}")
        # Confirm the record was created in the database
        created = self.env['res.users.approve'].sudo().search(
            [('email', '=', 'rpc_applicant@example.com')], limit=1)
        self.assertTrue(created)
        self.assertEqual(created.name, 'RPC Applicant')

    def test_09b_rpc_endpoint_disabled_when_feature_off(self):
        """RPC endpoint returns an error when signup approval is disabled"""
        self.config_param.set_bool(
            'website_signup_approval.auth_signup_approval', False)
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'id': 2,
            'params': {
                'username': 'Should Fail',
                'email': 'shouldfail@example.com',
                'password': 'Pw123!',
                'confirm_password': 'Pw123!',
                'data': [],
            },
        }
        res = self.url_open(
            '/web/signup/approve',
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        result = body.get('result', {})
        self.assertIn('error', result)

    def test_09c_rpc_endpoint_blocked_when_b2b(self):
        """RPC endpoint rejects uninvited signup when invitation scope is b2b"""
        self.config_param.set_str('auth_signup.invitation_scope', 'b2b')
        self.env['website'].search([]).write(
            {'auth_signup_uninvited': 'b2b'})
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'id': 3,
            'params': {
                'username': 'B2B Applicant',
                'email': 'b2b_applicant@example.com',
                'password': 'Password123!',
                'confirm_password': 'Password123!',
                'data': [],
            },
        }
        res = self.url_open(
            '/web/signup/approve',
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        result = body.get('result', {})
        self.assertIn('error', result)

    def test_09d_rpc_endpoint_required_documents_missing(self):
        """RPC endpoint rejects signup when required documents are missing"""
        doc = self.env['document.attachment'].create({
            'document': 'Passport',
        })
        self.config_param.set_str(
            'website_signup_approval.documents_ids',
            json.dumps([doc.id]))
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'id': 4,
            'params': {
                'username': 'Missing Docs Applicant',
                'email': 'missing_docs@example.com',
                'password': 'Password123!',
                'confirm_password': 'Password123!',
                'data': [],
            },
        }
        res = self.url_open(
            '/web/signup/approve',
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        result = body.get('result', {})
        self.assertIn('error', result)

    def test_09e_rpc_endpoint_required_documents_provided(self):
        """RPC endpoint succeeds when required documents are provided"""
        doc = self.env['document.attachment'].create({
            'document': 'National ID',
        })
        self.config_param.set_str(
            'website_signup_approval.documents_ids',
            json.dumps([doc.id]))
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'id': 5,
            'params': {
                'username': 'Valid Docs Applicant',
                'email': 'valid_docs@example.com',
                'password': 'Password123!',
                'confirm_password': 'Password123!',
                'data': ['data:image/png;base64,dGVzdF9kYXRh'],
            },
        }
        res = self.url_open(
            '/web/signup/approve',
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        result = body.get('result', {})
        self.assertTrue(
            result.get('success'),
            f"Expected success=True but got: {result}")
        created = self.env['res.users.approve'].sudo().search(
            [('email', '=', 'valid_docs@example.com')], limit=1)
        self.assertTrue(created)
        self.assertEqual(len(created.attachment_ids), 1)
