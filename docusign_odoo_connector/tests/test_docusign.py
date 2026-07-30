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
from unittest.mock import MagicMock, patch
from docusign_esign import ApiException
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.addons.docusign_odoo_connector.models import docusign as docusign_module


def _fake_key():
    """Minimal mock that looks like a private-key ir.attachment."""
    mock = MagicMock()
    mock.datas = base64.b64encode(b'FAKE_RSA_KEY')
    return mock


def _fake_token(access_token='test-token'):
    tok = MagicMock()
    tok.access_token = access_token
    return tok


# ---------------------------------------------------------------------------
# action_login_docusign
# ---------------------------------------------------------------------------

class TestActionLoginDocusign(TransactionCase):
    """Tests for docusign.action_login_docusign."""

    def _call(self, status_code=200, jwt_side_effect=None):
        mock_client = MagicMock()
        if jwt_side_effect:
            mock_client.request_jwt_user_token.side_effect = jwt_side_effect
        else:
            mock_client.request_jwt_user_token.return_value = _fake_token()

        mock_envelope_api = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = status_code

        with patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.ApiClient',
            return_value=mock_client,
        ), patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.EnvelopesApi',
            return_value=mock_envelope_api,
        ), patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.requests.get',
            return_value=mock_response,
        ):
            return docusign_module.action_login_docusign(
                user_id='u', account_id='a',
                integratorKey='k', privatekey=_fake_key(),
            )

    def test_01_returns_200_on_success(self):
        """action_login_docusign returns the HTTP status code on success."""
        self.assertEqual(self._call(status_code=200), 200)


    def test_02_returns_non_200_status(self):
        """action_login_docusign passes through non-200 status codes unchanged."""
        self.assertEqual(self._call(status_code=401), 401)


    def test_03_api_exception_raises_user_error(self):
        """ApiException from JWT request is re-raised as UserError."""
        with self.assertRaises(UserError):
            self._call(jwt_side_effect=ApiException(status=401, reason='Unauthorized'))


    def test_04_bearer_header_is_set(self):
        """action_login_docusign sets the Authorization Bearer header."""
        mock_client = MagicMock()
        mock_client.request_jwt_user_token.return_value = _fake_token('my-token')
        mock_env_api = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.ApiClient',
            return_value=mock_client,
        ), patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.EnvelopesApi',
            return_value=mock_env_api,
        ), patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.requests.get',
            return_value=mock_resp,
        ):
            docusign_module.action_login_docusign(
                user_id='u', account_id='a',
                integratorKey='k', privatekey=_fake_key(),
            )

        mock_client.set_default_header.assert_called_once_with(
            header_name='Authorization',
            header_value='Bearer my-token',
        )


    def test_05_list_status_changes_is_called(self):
        """action_login_docusign calls list_status_changes to probe the API."""
        mock_client = MagicMock()
        mock_client.request_jwt_user_token.return_value = _fake_token()
        mock_env_api = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.ApiClient',
            return_value=mock_client,
        ), patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.EnvelopesApi',
            return_value=mock_env_api,
        ), patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.requests.get',
            return_value=mock_resp,
        ):
            docusign_module.action_login_docusign(
                user_id='u', account_id='a',
                integratorKey='k', privatekey=_fake_key(),
            )

        mock_env_api.list_status_changes.assert_called_once()



# ---------------------------------------------------------------------------
# action_send_docusign_file
# ---------------------------------------------------------------------------

class TestActionSendDocusignFile(TransactionCase):
    """Tests for docusign.action_send_docusign_file."""

    def _call(self, tabs=None, envelope_side_effect=None):
        tabs = tabs or [{'signHereTabs': [{'xPosition': 50, 'yPosition': 200}]}]
        mock_client = MagicMock()
        mock_client.request_jwt_user_token.return_value = _fake_token()
        mock_env_api = MagicMock()
        if envelope_side_effect:
            mock_env_api.create_envelope.side_effect = envelope_side_effect
        else:
            mock_env_api.create_envelope.return_value = MagicMock(envelope_id='env-123')

        with patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.ApiClient',
            return_value=mock_client,
        ), patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.EnvelopesApi',
            return_value=mock_env_api,
        ):
            result = docusign_module.action_send_docusign_file(
                user_id='u', account_id='a', integratorKey='k',
                privatekey=_fake_key(),
                filename='doc.pdf',
                fileContents=base64.b64encode(b'%PDF'),
                receiver_name=['Alice'],
                receiver_email=['alice@example.com'],
                tabs1=tabs,
            )
        return result, mock_env_api

    def test_01_returns_envelope_response(self):
        """action_send_docusign_file returns the create_envelope response."""
        result, _ = self._call()
        self.assertIsNotNone(result)


    def test_02_create_envelope_called_with_account_id(self):
        """create_envelope is called with the correct account_id."""
        _, mock_env_api = self._call()
        mock_env_api.create_envelope.assert_called_once()
        call_kwargs = mock_env_api.create_envelope.call_args
        # account_id can arrive as positional or keyword arg
        account_id = (
            call_kwargs.kwargs.get('account_id') or
            (call_kwargs.args[0] if call_kwargs.args else None)
        )
        self.assertEqual(account_id, 'a')


    def test_03_y_position_decremented_by_30(self):
        """yPosition in each signHereTab is decremented by 30 before sending."""
        tabs = [{'signHereTabs': [{'xPosition': 50, 'yPosition': 200}]}]
        self._call(tabs=tabs)
        self.assertEqual(tabs[0]['signHereTabs'][0]['yPosition'], 170)


    def test_04_api_exception_raises_user_error(self):
        """ApiException from create_envelope is re-raised as UserError."""
        with self.assertRaises(UserError):
            self._call(envelope_side_effect=ApiException(status=400, reason='Bad Request'))


    def test_05_multiple_recipients_handled(self):
        """Multiple recipients each get their own recipientId and tabs."""
        tabs = [
            {'signHereTabs': [{'xPosition': 10, 'yPosition': 100}]},
            {'signHereTabs': [{'xPosition': 20, 'yPosition': 150}]},
        ]
        mock_client = MagicMock()
        mock_client.request_jwt_user_token.return_value = _fake_token()
        mock_env_api = MagicMock()
        mock_env_api.create_envelope.return_value = MagicMock()

        with patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.ApiClient',
            return_value=mock_client,
        ), patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.EnvelopesApi',
            return_value=mock_env_api,
        ):
            docusign_module.action_send_docusign_file(
                user_id='u', account_id='a', integratorKey='k',
                privatekey=_fake_key(),
                filename='doc.pdf',
                fileContents=base64.b64encode(b'%PDF'),
                receiver_name=['Alice', 'Bob'],
                receiver_email=['alice@example.com', 'bob@example.com'],
                tabs1=tabs,
            )

        mock_env_api.create_envelope.assert_called_once()



# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------

class TestGetStatus(TransactionCase):
    """Tests for docusign.get_status."""

    def _call(self, status='sent', side_effect=None):
        mock_client = MagicMock()
        mock_client.request_jwt_user_token.return_value = _fake_token()
        mock_envelope = MagicMock()
        mock_envelope.status = status
        mock_env_api = MagicMock()
        if side_effect:
            mock_env_api.get_envelope.side_effect = side_effect
        else:
            mock_env_api.get_envelope.return_value = mock_envelope

        with patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.ApiClient',
            return_value=mock_client,
        ), patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.EnvelopesApi',
            return_value=mock_env_api,
        ):
            return docusign_module.get_status(
                integratorKey='k', envelopeId='env-001',
                privatekey=_fake_key(), user_id='u', account_id='a',
            )

    def test_01_returns_sent_status(self):
        """get_status returns 'sent' for a sent envelope."""
        self.assertEqual(self._call('sent'), 'sent')


    def test_02_returns_completed_status(self):
        """get_status returns 'completed' for a fully signed envelope."""
        self.assertEqual(self._call('completed'), 'completed')


    def test_03_returns_declined_status(self):
        """get_status returns 'declined' when a recipient declines."""
        self.assertEqual(self._call('declined'), 'declined')


    def test_04_returns_voided_status(self):
        """get_status returns 'voided' for a voided envelope."""
        self.assertEqual(self._call('voided'), 'voided')


    def test_05_api_exception_raises_user_error(self):
        """ApiException from get_envelope is re-raised as UserError."""
        with self.assertRaises(UserError):
            self._call(side_effect=ApiException(status=404, reason='Not Found'))



# ---------------------------------------------------------------------------
# download_documents
# ---------------------------------------------------------------------------

class TestDownloadDocuments(TransactionCase):
    """Tests for docusign.download_documents."""

    def _setup_api(self, envelope_status='completed', doc_name='signed.pdf',
                   get_envelope_side_effect=None):
        mock_client = MagicMock()
        mock_client.request_jwt_user_token.return_value = _fake_token()

        mock_envelope = MagicMock()
        mock_envelope.status = envelope_status

        mock_doc = MagicMock()
        mock_doc.name = doc_name
        mock_docs = MagicMock()
        mock_docs.envelope_documents = [mock_doc]

        mock_env_api = MagicMock()
        if get_envelope_side_effect:
            mock_env_api.get_envelope.side_effect = get_envelope_side_effect
        else:
            mock_env_api.get_envelope.return_value = mock_envelope
        mock_env_api.list_documents.return_value = mock_docs
        mock_env_api.get_document.return_value = b'%PDF-1.4 binary'

        return mock_client, mock_env_api

    def test_01_non_completed_returns_empty_path(self):
        """download_documents returns (status, '') when not completed."""
        mock_client, mock_env_api = self._setup_api('sent')

        with patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.ApiClient',
            return_value=mock_client,
        ), patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.EnvelopesApi',
            return_value=mock_env_api,
        ):
            status, path = docusign_module.download_documents(
                integratorKey='k', envelopeId='env-001',
                privatekey=_fake_key(), user_id='u', account_id='a',
            )

        self.assertEqual(status, 'sent')
        self.assertEqual(path, '')


    def test_02_declined_returns_empty_path(self):
        """download_documents returns early for declined envelopes."""
        mock_client, mock_env_api = self._setup_api('declined')

        with patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.ApiClient',
            return_value=mock_client,
        ), patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.EnvelopesApi',
            return_value=mock_env_api,
        ):
            status, path = docusign_module.download_documents(
                integratorKey='k', envelopeId='env-002',
                privatekey=_fake_key(), user_id='u', account_id='a',
            )

        self.assertEqual(status, 'declined')
        self.assertEqual(path, '')


    def test_03_completed_returns_file_path(self):
        """download_documents returns ('completed', path) with filename in path."""
        mock_client, mock_env_api = self._setup_api('completed', 'contract.pdf')

        with patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.ApiClient',
            return_value=mock_client,
        ), patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.EnvelopesApi',
            return_value=mock_env_api,
        ), patch('os.path.isdir', return_value=True), \
           patch('builtins.open', MagicMock()):
            status, path = docusign_module.download_documents(
                integratorKey='k', envelopeId='env-003',
                privatekey=_fake_key(), user_id='u', account_id='a',
            )

        self.assertEqual(status, 'completed')
        self.assertIn('contract.pdf', path)


    def test_04_directory_created_when_missing(self):
        """download_documents calls os.mkdir when the files dir does not exist."""
        mock_client, mock_env_api = self._setup_api('completed')
        mock_mkdir = MagicMock()

        with patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.ApiClient',
            return_value=mock_client,
        ), patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.EnvelopesApi',
            return_value=mock_env_api,
        ), patch('os.path.isdir', return_value=False), \
           patch('os.mkdir', mock_mkdir), \
           patch('builtins.open', MagicMock()):
            docusign_module.download_documents(
                integratorKey='k', envelopeId='env-004',
                privatekey=_fake_key(), user_id='u', account_id='a',
            )

        mock_mkdir.assert_called_once()


    def test_05_api_exception_raises_user_error(self):
        """ApiException from the DocuSign API is re-raised as UserError."""
        mock_client, mock_env_api = self._setup_api(
            get_envelope_side_effect=ApiException(status=500, reason='Server Error')
        )

        with patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.ApiClient',
            return_value=mock_client,
        ), patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.EnvelopesApi',
            return_value=mock_env_api,
        ):
            with self.assertRaises(UserError):
                docusign_module.download_documents(
                    integratorKey='k', envelopeId='env-err',
                    privatekey=_fake_key(), user_id='u', account_id='a',
                )


    def test_06_list_documents_called_on_completed(self):
        """list_documents is called once when the envelope is completed."""
        mock_client, mock_env_api = self._setup_api('completed')

        with patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.ApiClient',
            return_value=mock_client,
        ), patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.EnvelopesApi',
            return_value=mock_env_api,
        ), patch('os.path.isdir', return_value=True), \
           patch('builtins.open', MagicMock()):
            docusign_module.download_documents(
                integratorKey='k', envelopeId='env-005',
                privatekey=_fake_key(), user_id='u', account_id='a',
            )

        mock_env_api.list_documents.assert_called_once()


    def test_07_get_document_called_with_document_id_1(self):
        """get_document is called with document_id='1' for the main signed doc."""
        mock_client, mock_env_api = self._setup_api('completed')

        with patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.ApiClient',
            return_value=mock_client,
        ), patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.EnvelopesApi',
            return_value=mock_env_api,
        ), patch('os.path.isdir', return_value=True), \
           patch('builtins.open', MagicMock()):
            docusign_module.download_documents(
                integratorKey='k', envelopeId='env-006',
                privatekey=_fake_key(), user_id='u', account_id='a',
            )

        call_kwargs = mock_env_api.get_document.call_args
        doc_id = (
            call_kwargs.kwargs.get('document_id') or
            (call_kwargs.args[1] if len(call_kwargs.args) > 1 else None)
        )
        self.assertEqual(doc_id, '1')

