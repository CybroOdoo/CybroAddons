# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil @ cybrosys,(odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
import base64
from unittest.mock import patch
from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestDocusignCredentials(TransactionCase):
    """Test suite for the docusign.credentials model."""

    def setUp(self):
        super().setUp()
        self.Credentials = self.env['docusign.credentials']

        # Create a minimal RSA key attachment (fake content — no real API calls)
        self.fake_key = self.env['ir.attachment'].create({
            'name': 'fake_private.key',
            'datas': base64.b64encode(b'FAKE_PRIVATE_KEY_CONTENT'),
            'mimetype': 'application/octet-stream',
        })

    def _make_credentials(self, **kwargs):
        """Helper: build a valid docusign.credentials record."""
        vals = {
            'name': 'Test Credentials',
            'integrator_key': 'test-integrator-key-uuid',
            'account_id_data': 'test-account-id',
            'user_id_data': 'test-user-id',
            'private_key_ids': [Command.link(self.fake_key.id)],
        }
        vals.update(kwargs)
        return self.Credentials.create(vals)

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------

    def test_01_create_credentials_minimal(self):
        """Create a minimal docusign.credentials record and verify all fields."""
        cred = self._make_credentials()
        self.assertTrue(cred.id)
        self.assertEqual(cred.name, 'Test Credentials')
        self.assertEqual(cred.integrator_key, 'test-integrator-key-uuid')
        self.assertEqual(cred.account_id_data, 'test-account-id')
        self.assertEqual(cred.user_id_data, 'test-user-id')
        self.assertIn(self.fake_key, cred.private_key_ids)

    def test_02_default_company_id(self):
        """company_id should default to the current user's company."""
        cred = self._make_credentials()
        self.assertEqual(cred.company_id, self.env.user.company_id)

    def test_03_write_credentials_name(self):
        """Updating name via write persists correctly."""
        cred = self._make_credentials()
        cred.write({'name': 'Updated Name'})
        self.assertEqual(cred.name, 'Updated Name')

    def test_04_write_integrator_key(self):
        """Updating integrator_key via write persists correctly."""
        cred = self._make_credentials()
        cred.write({'integrator_key': 'new-integrator-key'})
        self.assertEqual(cred.integrator_key, 'new-integrator-key')

    def test_05_unlink_credentials(self):
        """Deleting a credentials record removes it from the database."""
        cred = self._make_credentials()
        cred_id = cred.id
        cred.unlink()
        self.assertFalse(self.Credentials.search([('id', '=', cred_id)]))

    # -------------------------------------------------------------------------
    # Required field constraints
    # -------------------------------------------------------------------------

    def test_06_name_is_required(self):
        """Creating a record without name must raise an exception."""
        with self.assertRaises(Exception):
            self.Credentials.create({
                'integrator_key': 'k',
                'account_id_data': 'a',
                'user_id_data': 'u',
                'private_key_ids': [Command.link(self.fake_key.id)],
            })

    def test_07_integrator_key_is_required(self):
        """Creating a record without integrator_key must raise an exception."""
        with self.assertRaises(Exception):
            self.Credentials.create({
                'name': 'No Key',
                'account_id_data': 'a',
                'user_id_data': 'u',
                'private_key_ids': [Command.link(self.fake_key.id)],
            })

    def test_08_account_id_data_is_required(self):
        """Creating a record without account_id_data must raise an exception."""
        with self.assertRaises(Exception):
            self.Credentials.create({
                'name': 'No Account',
                'integrator_key': 'k',
                'user_id_data': 'u',
                'private_key_ids': [Command.link(self.fake_key.id)],
            })

    def test_09_user_id_data_is_required(self):
        """Creating a record without user_id_data must raise an exception."""
        with self.assertRaises(Exception):
            self.Credentials.create({
                'name': 'No User',
                'integrator_key': 'k',
                'account_id_data': 'a',
                'private_key_ids': [Command.link(self.fake_key.id)],
            })

    # -------------------------------------------------------------------------
    # _check_private_key_ids constraint
    # -------------------------------------------------------------------------

    def test_10_constraint_one_private_key_allowed(self):
        """Exactly one RSA key attachment is valid — no ValidationError raised."""
        cred = self._make_credentials()
        self.assertEqual(len(cred.private_key_ids), 1)

    def test_11_constraint_two_private_keys_raises(self):
        """Uploading more than one RSA key must raise ValidationError."""
        second_key = self.env['ir.attachment'].create({
            'name': 'second_key.pem',
            'datas': base64.b64encode(b'SECOND_KEY'),
            'mimetype': 'application/octet-stream',
        })
        with self.assertRaises(ValidationError):
            self._make_credentials(
                private_key_ids=[
                    Command.link(self.fake_key.id),
                    Command.link(second_key.id),
                ]
            )

    def test_12_constraint_zero_private_keys_allowed(self):
        """Zero RSA keys should not trigger the > 1 constraint."""
        cred = self.Credentials.create({
            'name': 'No Key Cred',
            'integrator_key': 'k',
            'account_id_data': 'a',
            'user_id_data': 'u',
        })
        self.assertFalse(cred.private_key_ids)

    # -------------------------------------------------------------------------
    # action_test_credentials — mocked
    # -------------------------------------------------------------------------

    def test_13_action_test_credentials_success(self):
        """action_test_credentials returns a display_notification action on HTTP 200."""
        cred = self._make_credentials()
        with patch(
            'odoo.addons.docusign_odoo_connector.models.docusign_credentials.docusign.action_login_docusign',
            return_value=200,
        ):
            result = cred.action_test_credentials()
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertEqual(result['params']['type'], 'success')

    def test_14_action_test_credentials_failure_raises_user_error(self):
        """action_test_credentials raises UserError when API returns non-200."""
        cred = self._make_credentials()
        with patch(
            'odoo.addons.docusign_odoo_connector.models.docusign_credentials.docusign.action_login_docusign',
            return_value=401,
        ):
            with self.assertRaises(UserError):
                cred.action_test_credentials()

    def test_15_action_test_credentials_passes_correct_args(self):
        """action_test_credentials forwards the right credential values to the helper."""
        cred = self._make_credentials()
        with patch(
            'odoo.addons.docusign_odoo_connector.models.docusign_credentials.docusign.action_login_docusign',
            return_value=200,
        ) as mock_login:
            cred.action_test_credentials()
        mock_login.assert_called_once_with(
            cred.user_id_data,
            cred.account_id_data,
            cred.integrator_key,
            cred.private_key_ids,
        )

    # -------------------------------------------------------------------------
    # Model metadata
    # -------------------------------------------------------------------------

    def test_16_model_name(self):
        """Model technical name must be 'docusign.credentials'."""
        self.assertEqual(self.env['docusign.credentials']._name, 'docusign.credentials')

    def test_17_model_description(self):
        """Model description must match the class docstring."""
        self.assertEqual(
            self.env['docusign.credentials']._description,
            'Docusign Credentials Setup',
        )
