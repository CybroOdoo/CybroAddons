# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
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
###############################################################################
from unittest.mock import patch
import requests
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestResPartner(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.user.company_id
        cls.company.contact_company_access_token = 'token_abc'

        cls.partner = cls.env['res.partner'].create({
            'name': 'Alice Smith',
            'first_name': 'Alice',
            'last_name': 'Smith',
            'email': 'alice@example.com',
            'phone': '+15550100',
            'street': '789 Broadway',
            'city': 'New York',
            'zip': '10003',
        })

    def test_01_action_export_google_contacts_new_success(self):
        """Test exporting a new contact to Google successfully."""
        mock_response = {
            'resourceName': 'people/c7777777',
            'etag': 'etag_new_1',
        }
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            ctx = {'uid': self.env.uid, 'active_ids': self.partner.ids}
            self.partner.with_context(ctx).action_export_google_contacts()

            self.assertEqual(self.partner.google_resource, 'people/c7777777')
            self.assertEqual(self.partner.google_etag, 'etag_new_1')

    def test_02_action_export_google_contacts_new_failure(self):
        """Test exporting new contact when Google API returns non-200."""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 400
            mock_post.return_value.text = 'Bad Request'

            ctx = {'uid': self.env.uid, 'active_ids': self.partner.ids}
            with self.assertRaises(ValidationError) as ctx_err:
                self.partner.with_context(ctx).action_export_google_contacts()
            self.assertIn("Failed to export contact", str(ctx_err.exception))

    def test_03_action_export_google_contacts_new_network_error(self):
        """Test exporting new contact when requests raises ConnectionError."""
        with patch('requests.post', side_effect=requests.exceptions.RequestException("Connection error")):
            ctx = {'uid': self.env.uid, 'active_ids': self.partner.ids}
            with self.assertRaises(ValidationError) as ctx_err:
                self.partner.with_context(ctx).action_export_google_contacts()
            self.assertIn("Network error while creating contact", str(ctx_err.exception))

    def test_04_action_export_google_contacts_update_success(self):
        """Test updating an existing contact in Google successfully."""
        self.partner.write({
            'google_resource': 'people/c7777777',
            'google_etag': 'etag_new_1',
        })
        mock_response = {
            'resourceName': 'people/c7777777',
            'etag': 'etag_new_2',
        }
        with patch('requests.patch') as mock_patch:
            mock_patch.return_value.status_code = 200
            mock_patch.return_value.json.return_value = mock_response

            ctx = {'uid': self.env.uid, 'active_ids': self.partner.ids}
            self.partner.with_context(ctx).action_export_google_contacts()

            self.assertEqual(self.partner.google_resource, 'people/c7777777')
            self.assertEqual(self.partner.google_etag, 'etag_new_2')

    def test_05_action_export_google_contacts_update_recreate_success(self):
        """Test updating contact that was deleted in Google (404) triggers recreation."""
        self.partner.write({
            'google_resource': 'people/c7777777',
            'google_etag': 'etag_new_1',
        })
        mock_recreate_response = {
            'resourceName': 'people/c8888888',
            'etag': 'etag_recreated',
        }
        with patch('requests.patch') as mock_patch, patch('requests.post') as mock_post:
            mock_patch.return_value.status_code = 404
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_recreate_response

            ctx = {'uid': self.env.uid, 'active_ids': self.partner.ids}
            self.partner.with_context(ctx).action_export_google_contacts()

            self.assertEqual(self.partner.google_resource, 'people/c8888888')
            self.assertEqual(self.partner.google_etag, 'etag_recreated')

    def test_06_action_export_google_contacts_update_recreate_failure(self):
        """Test updating contact deleted in Google when recreation fails."""
        self.partner.write({
            'google_resource': 'people/c7777777',
            'google_etag': 'etag_new_1',
        })
        with patch('requests.patch') as mock_patch, patch('requests.post') as mock_post:
            mock_patch.return_value.status_code = 404
            mock_post.return_value.status_code = 400
            mock_post.return_value.text = 'Failed recreation'

            ctx = {'uid': self.env.uid, 'active_ids': self.partner.ids}
            with self.assertRaises(ValidationError) as ctx_err:
                self.partner.with_context(ctx).action_export_google_contacts()
            self.assertIn("Failed to recreate contact", str(ctx_err.exception))

    def test_07_action_export_google_contacts_update_failure(self):
        """Test updating existing contact when Google API returns non-200/404."""
        self.partner.write({
            'google_resource': 'people/c7777777',
            'google_etag': 'etag_new_1',
        })
        with patch('requests.patch') as mock_patch:
            mock_patch.return_value.status_code = 500
            mock_patch.return_value.text = 'Internal Error'

            ctx = {'uid': self.env.uid, 'active_ids': self.partner.ids}
            with self.assertRaises(ValidationError) as ctx_err:
                self.partner.with_context(ctx).action_export_google_contacts()
            self.assertIn("Failed to update contact", str(ctx_err.exception))

    def test_08_action_export_google_contacts_update_network_error(self):
        """Test updating existing contact when network request fails."""
        self.partner.write({
            'google_resource': 'people/c7777777',
            'google_etag': 'etag_new_1',
        })
        with patch('requests.patch', side_effect=requests.exceptions.RequestException("Connection error")):
            ctx = {'uid': self.env.uid, 'active_ids': self.partner.ids}
            with self.assertRaises(ValidationError) as ctx_err:
                self.partner.with_context(ctx).action_export_google_contacts()
            self.assertIn("Network error while syncing contact", str(ctx_err.exception))

    def test_09_action_delete_google_contact_no_resource(self):
        """Test deleting contact from Google when local partner has no Google Contact ID."""
        self.partner.write({
            'google_resource': False,
            'google_etag': False,
        })
        ctx = {'uid': self.env.uid, 'active_ids': self.partner.ids}
        self.partner.with_context(ctx).action_delete_google_contact()
        self.assertTrue(self.partner.exists())

    def test_10_action_delete_google_contact_success(self):
        """Test deleting contact from Google successfully unlinks local record."""
        self.partner.write({
            'google_resource': 'people/c7777777',
            'google_etag': 'etag_new_1',
        })
        with patch('requests.delete') as mock_del:
            mock_del.return_value.status_code = 200

            ctx = {'uid': self.env.uid, 'active_ids': self.partner.ids}
            self.partner.with_context(ctx).action_delete_google_contact()

            self.assertFalse(self.partner.exists())

    def test_11_action_delete_google_contact_not_found(self):
        """Test deleting contact from Google when Google Contact is already deleted (404) clears local references."""
        self.partner.write({
            'google_resource': 'people/c7777777',
            'google_etag': 'etag_new_1',
        })
        with patch('requests.delete') as mock_del:
            mock_del.return_value.status_code = 404

            ctx = {'uid': self.env.uid, 'active_ids': self.partner.ids}
            self.partner.with_context(ctx).action_delete_google_contact()

            self.assertTrue(self.partner.exists())
            self.assertFalse(self.partner.google_resource)
            self.assertFalse(self.partner.google_etag)

    def test_12_action_delete_google_contact_failure(self):
        """Test deleting contact from Google raises ValidationError when API returns non-200/404."""
        self.partner.write({
            'google_resource': 'people/c7777777',
            'google_etag': 'etag_new_1',
        })
        with patch('requests.delete') as mock_del:
            mock_del.return_value.status_code = 400
            mock_del.return_value.text = 'Bad Request'

            ctx = {'uid': self.env.uid, 'active_ids': self.partner.ids}
            with self.assertRaises(ValidationError) as ctx_err:
                self.partner.with_context(ctx).action_delete_google_contact()
            self.assertIn("Failed to delete contact", str(ctx_err.exception))
