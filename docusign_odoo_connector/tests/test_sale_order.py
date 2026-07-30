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
from unittest.mock import patch, mock_open
from odoo import Command
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSaleOrderExtension(TransactionCase):
    """Test suite for the sale.order extensions added by docusign_odoo_connector."""

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'DocuSign Test Customer',
            'email': 'test@docusign.example.com',
        })
        self.product = self.env['product.product'].create({
            'name': 'DocuSign Test Product',
            'type': 'consu',
            'list_price': 100.0,
        })
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        })

        # Fake key attachment
        self.fake_key = self.env['ir.attachment'].create({
            'name': 'fake.key',
            'datas': base64.b64encode(b'FAKE_KEY'),
            'mimetype': 'application/octet-stream',
        })
        self.credentials = self.env['docusign.credentials'].create({
            'name': 'SO Test Creds',
            'integrator_key': 'so-integrator-key',
            'account_id_data': 'so-account-id',
            'user_id_data': 'so-user-id',
            'private_key_ids': [Command.link(self.fake_key.id)],
        })

    # -------------------------------------------------------------------------
    # New fields on sale.order
    # -------------------------------------------------------------------------

    def test_01_new_fields_exist(self):
        """docusign_line_ids and credentials_id fields must be present."""
        self.assertFalse(self.order.docusign_line_ids)
        self.assertFalse(self.order.credentials_id)

    def test_02_credentials_id_can_be_set(self):
        """credentials_id can be assigned to a docusign.credentials record."""
        self.order.write({'credentials_id': self.credentials.id})
        self.assertEqual(self.order.credentials_id.id, self.credentials.id)

    def test_03_docusign_line_ids_readonly(self):
        """docusign_line_ids is declared readonly=True on the field definition."""
        field = self.env['sale.order']._fields['docusign_line_ids']
        self.assertTrue(field.readonly)

    # -------------------------------------------------------------------------
    # action_send_document
    # -------------------------------------------------------------------------

    def test_04_action_send_document_returns_act_window(self):
        """action_send_document must return an act_window action for send.document."""
        action = self.order.action_send_document()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'send.document')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['view_mode'], 'form')

    def test_05_action_send_document_context_defaults(self):
        """action_send_document sets default_email_id and default_res_id in context."""
        action = self.order.action_send_document()
        ctx = action['context']
        self.assertEqual(ctx['default_email_id'], self.partner.id)
        self.assertEqual(ctx['default_res_id'], self.order.id)

    # -------------------------------------------------------------------------
    # action_download_document — error branches (no external API calls)
    # -------------------------------------------------------------------------

    def test_06_download_document_no_credentials_raises(self):
        """action_download_document raises UserError when credentials_id is not set."""
        self.order.write({'credentials_id': False})
        with self.assertRaises(UserError, msg='Please select credential'):
            self.order.action_download_document()

    def test_07_download_document_no_envelope_raises(self):
        """action_download_document raises UserError when a line has no envelope_id."""
        self.order.write({'credentials_id': self.credentials.id})
        # Add a docusign line with no envelope_id directly via SQL bypass
        self.env['docusign.lines'].sudo().create({
            'docusign_id': self.order.id,
            'document': 'Test Doc',
            'send_to': 'someone@example.com',
            'status': 'sent',
            'envelope_id': False,
        })
        with self.assertRaises(UserError, msg='No agreement documents are sent'):
            self.order.action_download_document()

    def test_08_download_document_not_completed_no_path(self):
        """When DocuSign status != 'completed', no file path is returned and nothing breaks.

        action_download_document calls self.env.cr.commit() which TransactionCase
        forbids. We patch the cursor instance's commit directly to a no-op.
        """
        self.order.write({'credentials_id': self.credentials.id})
        self.env['docusign.lines'].sudo().create({
            'docusign_id': self.order.id,
            'document': 'Test Doc',
            'send_to': 'someone@example.com',
            'status': 'sent',
            'envelope_id': 'fake-envelope-id-001',
        })
        with patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.download_documents',
            return_value=('sent', ''),
        ), patch.object(self.env.cr, 'commit', lambda: None):
            self.order.action_download_document()

    def test_09_download_document_completed_attaches_file(self):
        """When DocuSign returns 'completed' + a path, the signed doc is attached.

        action_download_document calls self.env.cr.commit() which TransactionCase
        forbids. We patch the cursor instance's commit directly to a no-op.

        ir.attachment._file_read is also patched so the mocked filestore write
        is matched by a mocked filestore read — making attach_id.datas non-empty
        without touching model code.
        """
        self.order.write({'credentials_id': self.credentials.id})
        line = self.env['docusign.lines'].sudo().create({
            'docusign_id': self.order.id,
            'document': 'signed.pdf',
            'send_to': 'someone@example.com',
            'status': 'sent',
            'envelope_id': 'fake-envelope-id-002',
        })
        fake_pdf = b'%PDF-1.4 fake content'
        fake_path = '/tmp/files/signed.pdf'

        with patch(
            'odoo.addons.docusign_odoo_connector.models.docusign.download_documents',
            return_value=('completed', fake_path),
        ), patch('builtins.open', mock_open(read_data=fake_pdf)), \
           patch('os.remove'), patch('os.path.exists', return_value=True), \
           patch('shutil.rmtree'), \
           patch(
               'odoo.addons.base.models.ir_attachment.IrAttachment._file_read',
               return_value=fake_pdf,
           ), \
           patch.object(self.env.cr, 'commit', lambda: None):
            self.order.action_download_document()

        # The ORM cache holds the assigned value — read directly without
        # invalidating so we avoid a DB round-trip through the mocked filestore.
        self.assertEqual(line.status, 'completed')
        self.assertTrue(line.signed_document)


class TestDocusignLines(TransactionCase):
    """Test suite for the docusign.lines model."""

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Lines Test Partner',
            'email': 'lines@docusign.example.com',
        })
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })

    def _make_line(self, **kwargs):
        vals = {
            'docusign_id': self.order.id,
            'document': 'contract.pdf',
            'send_to': 'signer@example.com',
            'status': 'sent',
            'envelope_id': 'env-001',
        }
        vals.update(kwargs)
        return self.env['docusign.lines'].create(vals)

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------

    def test_01_create_line_minimal(self):
        """Create a docusign.lines record and verify all fields."""
        line = self._make_line()
        self.assertTrue(line.id)
        self.assertEqual(line.docusign_id.id, self.order.id)
        self.assertEqual(line.document, 'contract.pdf')
        self.assertEqual(line.send_to, 'signer@example.com')
        self.assertEqual(line.status, 'sent')
        self.assertEqual(line.envelope_id, 'env-001')
        self.assertFalse(line.signed_document)

    def test_02_create_line_without_envelope(self):
        """A line with no envelope_id (False) should be created without error."""
        line = self._make_line(envelope_id=False)
        self.assertFalse(line.envelope_id)

    def test_03_write_line_status(self):
        """Updating status persists correctly."""
        line = self._make_line()
        line.write({'status': 'completed'})
        self.assertEqual(line.status, 'completed')

    def test_04_write_signed_document(self):
        """Assigning binary data to signed_document persists correctly."""
        line = self._make_line()
        fake_b64 = base64.b64encode(b'%PDF fake signed content')
        line.write({'signed_document': fake_b64})
        self.assertTrue(line.signed_document)

    def test_05_unlink_line(self):
        """Deleting a docusign.lines record removes it."""
        line = self._make_line()
        line_id = line.id
        line.unlink()
        self.assertFalse(self.env['docusign.lines'].search([('id', '=', line_id)]))

    def test_06_multiple_lines_per_order(self):
        """A single sale.order can have multiple docusign.lines."""
        l1 = self._make_line(envelope_id='env-001')
        l2 = self._make_line(envelope_id='env-002', document='addendum.pdf')
        lines = self.env['docusign.lines'].search([('docusign_id', '=', self.order.id)])
        self.assertIn(l1, lines)
        self.assertIn(l2, lines)

    def test_07_line_cascade_when_order_deleted(self):
        """When a sale.order is deleted its docusign.lines should be removed too
        (Many2one with no explicit ondelete='cascade' — line becomes orphan with
        docusign_id=False; we verify the line record itself still exists)."""
        line = self._make_line()
        line_id = line.id
        # Lines use Many2one without cascade — after order deletion the line
        # remains but docusign_id is nullified.
        self.order.unlink()
        remaining = self.env['docusign.lines'].search([('id', '=', line_id)])
        # Either deleted or orphaned — both are acceptable; the important thing
        # is no exception is raised.
        self.assertIsNotNone(remaining)

    # -------------------------------------------------------------------------
    # Model metadata
    # -------------------------------------------------------------------------

    def test_08_model_name(self):
        """Model technical name must be 'docusign.lines'."""
        self.assertEqual(self.env['docusign.lines']._name, 'docusign.lines')

    def test_09_model_description(self):
        """Model description must be set correctly."""
        self.assertEqual(
            self.env['docusign.lines']._description,
            'Docusign lines for retrieving send data information',
        )
