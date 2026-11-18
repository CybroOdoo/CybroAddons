# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#############################################################################
from unittest.mock import patch
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from .common import mock_response


@tagged('post_install', '-at_install')
class TestResPartner(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write({'api_key': 'test_api_key', 'contact_synced': False})
        cls.partner = cls.env['res.partner'].create({
            'name': 'Pipedrive Partner',
            'pipedrive_reference': '5501',
        })
        cls.env['pipedrive.record'].create({
            'pipedrive_reference': '5501',
            'record_type': 'partner',
            'odoo_ref': cls.partner.id,
        })

    @patch('requests.post')
    def test_create_partner(self, mock_post):
        """New contacts are created in Pipedrive once contacts are synced."""
        self.company.contact_synced = True
        mock_post.return_value = mock_response(
            {'success': True, 'data': {'id': 5502}})
        partner = self.env['res.partner'].create(
            {'name': 'New Contact', 'email': 'new@example.com'})
        self.assertEqual(partner.pipedrive_reference, '5502')
        self.assertTrue(self.env['pipedrive.record'].search(
            [('record_type', '=', 'partner'), ('odoo_ref', '=', partner.id)]))

    @patch('requests.post')
    def test_create_partner_not_synced(self, mock_post):
        """Nothing is sent before contacts are synced."""
        self.env['res.partner'].create({'name': 'Local Contact'})
        mock_post.assert_not_called()

    @patch('requests.post')
    def test_create_partner_with_reference(self, mock_post):
        """Contacts coming from Pipedrive are not sent back."""
        self.company.contact_synced = True
        self.env['res.partner'].create(
            {'name': 'Imported Contact', 'pipedrive_reference': '5503'})
        mock_post.assert_not_called()

    @patch('requests.post')
    def test_create_partner_error(self, mock_post):
        self.company.contact_synced = True
        mock_post.return_value = mock_response(
            {'success': False, 'error': 'Person not created'})
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({'name': 'Failing Contact'})

    @patch('requests.put')
    def test_write_partner(self, mock_put):
        mock_put.return_value = mock_response({'success': True})
        self.partner.write(
            {'name': 'Renamed Partner', 'email': 'renamed@example.com'})
        sent = mock_put.call_args.kwargs['json']
        self.assertEqual(sent['name'], 'Renamed Partner')
        self.assertEqual(sent['email'][0]['value'], 'renamed@example.com')

    @patch('requests.put')
    def test_write_partner_without_sync(self, mock_put):
        """Unrelated fields, unsynced partners and the skip flag do not
        call Pipedrive."""
        self.partner.write({'comment': 'Internal note'})
        self.env['res.partner'].create(
            {'name': 'Local Contact'}).write({'name': 'Still Local'})
        self.partner.with_context(skip_pipedrive_sync=True).write(
            {'name': 'Skipped'})
        mock_put.assert_not_called()

    @patch('requests.put')
    def test_write_partner_error(self, mock_put):
        mock_put.return_value = mock_response({'error': 'Person not found'})
        with self.assertRaises(ValidationError):
            self.partner.write({'name': 'Renamed Partner'})

    @patch('requests.delete')
    def test_unlink_partner(self, mock_delete):
        mock_delete.return_value = mock_response({'success': True})
        self.partner.unlink()
        self.assertFalse(self.partner.exists())
        mock_delete.assert_called_once()

    @patch('requests.delete')
    def test_unlink_partner_error(self, mock_delete):
        mock_delete.return_value = mock_response({'error': 'Person not found'})
        with self.assertRaises(ValidationError):
            self.partner.unlink()
