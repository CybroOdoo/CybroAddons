import base64
from unittest.mock import MagicMock, patch

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

from ..wizard import client_support


@tagged('post_install', '-at_install')
class TestClientSupport(TransactionCase):

    def _wizard(self, files=()):
        attachments = self.env['ir.attachment'].create([
            {'name': name, 'datas': base64.b64encode(raw)} for name, raw in files])
        return self.env['client.support'].create({
            'subject': 'Help', 'email': 'user@example.com',
            'attachment_ids': [(6, 0, attachments.ids)]})

    def _mock_post(self, result):
        response = MagicMock()
        response.json.return_value = {'result': result}
        return patch.object(client_support.requests, 'post', return_value=response)

    def test_api_key_sent(self):
        """Every request carries the module's API key header."""
        with self._mock_post({'message': 'success', 'ticket_id': 'CYB-1'}) as post:
            action = self._wizard().confirm_button()
        headers = post.call_args.kwargs['headers']
        self.assertEqual(headers['X-Cybrosys-Token'], client_support.SUPPORT_API_KEY)
        self.assertEqual(len(client_support.SUPPORT_API_KEY), 24)
        self.assertEqual(action['tag'], 'display_notification')

    def test_attachments_checked_before_sending(self):
        """Disallowed types, oversized files and too many files never reach the server."""
        cases = [
            [('drawing.svg', b'<svg/>')],
            [('big.pdf', b'%PDF' + b'0' * client_support.MAX_ATTACHMENT_SIZE)],
            [('f%s.pdf' % i, b'%PDF') for i in range(6)],
        ]
        for files in cases:
            with self._mock_post({}) as post, self.assertRaises(ValidationError):
                self._wizard(files).confirm_button()
            post.assert_not_called()

    def test_server_errors_explained(self):
        """Server error codes become clear messages."""
        expected = {
            'unauthorized': 'update the',
            'rate_limited': 'Too many support requests',
            'file_type_not_allowed': 'Only images',
        }
        for code, text in expected.items():
            with self._mock_post({'message': code}), self.assertRaises(ValidationError) as error:
                self._wizard().confirm_button()
            self.assertIn(text, str(error.exception))
