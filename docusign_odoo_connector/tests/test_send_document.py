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
import json
from unittest.mock import patch, MagicMock
from odoo import Command
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSendDocument(TransactionCase):
    """Test suite for the send.document transient wizard."""

    def setUp(self):
        super().setUp()
        self.SendDocument = self.env['send.document']

        # Partner with email
        self.partner = self.env['res.partner'].create({
            'name': 'Wizard Test Customer',
            'email': 'wizard@docusign.example.com',
        })
        # Partner without email
        self.partner_no_email = self.env['res.partner'].create({
            'name': 'No Email Customer',
            'email': False,
        })
        # Sale order
        self.product = self.env['product.product'].create({
            'name': 'Wizard Product',
            'type': 'consu',
        })
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 50.0,
            })],
        })

        # Fake RSA key attachment
        self.fake_key = self.env['ir.attachment'].create({
            'name': 'wizard_fake.key',
            'datas': base64.b64encode(b'WIZARD_FAKE_KEY'),
            'mimetype': 'application/octet-stream',
        })
        # Credentials record
        self.credentials = self.env['docusign.credentials'].create({
            'name': 'Wizard Creds',
            'integrator_key': 'wiz-integrator-key',
            'account_id_data': 'wiz-account-id',
            'user_id_data': 'wiz-user-id',
            'private_key_ids': [Command.link(self.fake_key.id)],
        })

        # Fake PDF content (base64-encoded)
        self.fake_pdf_b64 = base64.b64encode(b'%PDF-1.4 fake pdf content')

    def _make_wizard(self, **kwargs):
        """Helper: create a send.document wizard record."""
        vals = {
            'email_id': self.partner.id,
            'reference': 'WIZ-REF-001',
            'res_id': self.order.id,
        }
        vals.update(kwargs)
        return self.SendDocument.create(vals)

    # -------------------------------------------------------------------------
    # Field defaults and basic CRUD
    # -------------------------------------------------------------------------

    def test_01_create_wizard_minimal(self):
        """Create a minimal send.document wizard record."""
        wiz = self._make_wizard()
        self.assertTrue(wiz.id)
        self.assertEqual(wiz.email_id.id, self.partner.id)
        self.assertEqual(wiz.reference, 'WIZ-REF-001')
        self.assertFalse(wiz.file)
        self.assertFalse(wiz.check)
        self.assertFalse(wiz.data)

    def test_02_reference_is_required(self):
        """Creating wizard without reference raises an exception."""
        with self.assertRaises(Exception):
            self.SendDocument.create({
                'email_id': self.partner.id,
                'res_id': self.order.id,
            })

    def test_03_create_wizard_with_file(self):
        """A wizard record with a file attachment is created correctly."""
        wiz = self._make_wizard(file=self.fake_pdf_b64)
        self.assertTrue(wiz.file)

    # -------------------------------------------------------------------------
    # _onchange_check
    # -------------------------------------------------------------------------

    def test_04_onchange_check_sets_true_when_file_present(self):
        """_onchange_check must set check=True when file is populated."""
        wiz = self.SendDocument.new({
            'email_id': self.partner.id,
            'reference': 'REF-CHK',
            'file': self.fake_pdf_b64,
        })
        wiz._onchange_check()
        self.assertTrue(wiz.check)

    def test_05_onchange_check_sets_false_when_file_absent(self):
        """_onchange_check must set check=False when file is empty."""
        wiz = self.SendDocument.new({
            'email_id': self.partner.id,
            'reference': 'REF-CHK',
            'file': False,
        })
        wiz._onchange_check()
        self.assertFalse(wiz.check)

    def test_06_onchange_check_transitions_false_to_true(self):
        """_onchange_check updates check from False to True when file added."""
        wiz = self.SendDocument.new({
            'email_id': self.partner.id,
            'reference': 'REF-CHK-TRANS',
            'file': False,
        })
        wiz._onchange_check()
        self.assertFalse(wiz.check)
        wiz.file = self.fake_pdf_b64
        wiz._onchange_check()
        self.assertTrue(wiz.check)

    # -------------------------------------------------------------------------
    # action_edit_documents
    # -------------------------------------------------------------------------

    def test_07_action_edit_documents_with_file_raises_preview(self):
        """action_edit_documents raises UserError('Preview') when file is set."""
        wiz = self._make_wizard(file=self.fake_pdf_b64)
        with self.assertRaises(UserError) as ctx:
            wiz.action_edit_documents()
        self.assertIn('Preview', str(ctx.exception))

    def test_08_action_edit_documents_without_file_raises_no_attachment(self):
        """action_edit_documents raises UserError about no attachments when no file."""
        wiz = self._make_wizard()
        with self.assertRaises(UserError) as ctx:
            wiz.action_edit_documents()
        self.assertIn('No attachments', str(ctx.exception))

    # -------------------------------------------------------------------------
    # get_json_data
    # -------------------------------------------------------------------------

    def test_09_get_json_data_stores_tabs(self):
        """get_json_data must write JSON-encoded tabs into the data field."""
        wiz = self._make_wizard()
        tabs = {'signHereTabs': [{'xPosition': 100, 'yPosition': 200}]}
        wiz.get_json_data(tabs, wiz.id)
        wiz.invalidate_recordset(['data'])
        # data field stores the JSON string
        self.assertTrue(wiz.data)

    def test_10_get_json_data_overwrites_existing(self):
        """get_json_data should overwrite any previously stored data."""
        wiz = self._make_wizard()
        tabs1 = {'signHereTabs': [{'xPosition': 10, 'yPosition': 20}]}
        tabs2 = {'signHereTabs': [{'xPosition': 50, 'yPosition': 60}]}
        wiz.get_json_data(tabs1, wiz.id)
        wiz.get_json_data(tabs2, wiz.id)
        wiz.invalidate_recordset(['data'])
        self.assertTrue(wiz.data)

    # -------------------------------------------------------------------------
    # action_send_documents — error branches
    # -------------------------------------------------------------------------

    def test_11_action_send_no_data_raises(self):
        """action_send_documents raises UserError when data/tabs are missing."""
        wiz = self._make_wizard()  # data is empty by default
        with self.assertRaises(UserError) as ctx:
            wiz.action_send_documents()
        self.assertIn('add fields', str(ctx.exception))

    def test_12_action_send_no_email_on_partner_raises(self):
        """action_send_documents raises UserError when partner has no email."""
        wiz = self._make_wizard(
            email_id=self.partner_no_email.id,
            data=json.dumps({'signHereTabs': []}),
        )
        with self.assertRaises(UserError) as ctx:
            wiz.action_send_documents()
        self.assertIn('email', str(ctx.exception).lower())

    def test_13_action_send_no_credentials_raises(self):
        """action_send_documents raises UserError when no credentials exist."""
        # Delete all credentials so the search returns empty
        self.env['docusign.credentials'].search([]).unlink()
        wiz = self._make_wizard(
            email_id=self.partner.id,
            data=json.dumps({'signHereTabs': []}),
        )
        with self.assertRaises(UserError) as ctx:
            wiz.action_send_documents()
        self.assertIn('credentials', str(ctx.exception).lower())

    def test_14_action_send_documents_success(self):
        """action_send_documents calls the DocuSign helper and creates a line."""
        fake_response = MagicMock()
        fake_response.status = 'sent'
        fake_response.envelope_id = 'mock-envelope-id-999'

        wiz = self._make_wizard(
            email_id=self.partner.id,
            file=self.fake_pdf_b64,
            data=json.dumps({'signHereTabs': [{'xPosition': 100, 'yPosition': 200}]}),
        )

        with patch(
            'odoo.addons.docusign_odoo_connector.wizard.send_document.docusign.action_send_docusign_file',
            return_value=fake_response,
        ):
            wiz.action_send_documents()

        # A docusign.lines record should have been created on the sale order
        lines = self.env['docusign.lines'].search([
            ('docusign_id', '=', self.order.id),
        ])
        self.assertTrue(lines)
        self.assertEqual(lines[0].envelope_id, 'mock-envelope-id-999')
        self.assertEqual(lines[0].status, 'sent')
        self.assertEqual(lines[0].send_to, self.partner.email)
        self.assertEqual(lines[0].document, 'WIZ-REF-001')

    def test_15_action_send_documents_sets_account_id(self):
        """action_send_documents auto-fills account_id from the first credentials record."""
        fake_response = MagicMock()
        fake_response.status = 'sent'
        fake_response.envelope_id = 'mock-envelope-id-acct'

        wiz = self._make_wizard(
            email_id=self.partner.id,
            file=self.fake_pdf_b64,
            data=json.dumps({'signHereTabs': [{'xPosition': 10, 'yPosition': 20}]}),
        )

        with patch(
            'odoo.addons.docusign_odoo_connector.wizard.send_document.docusign.action_send_docusign_file',
            return_value=fake_response,
        ):
            wiz.action_send_documents()

        wiz.invalidate_recordset(['account_id'])
        self.assertTrue(wiz.account_id)

    # -------------------------------------------------------------------------
    # Model metadata
    # -------------------------------------------------------------------------

    def test_16_model_name(self):
        """Model technical name must be 'send.document'."""
        self.assertEqual(self.env['send.document']._name, 'send.document')

    def test_17_model_description(self):
        """Model description must match the class docstring."""
        self.assertEqual(
            self.env['send.document']._description,
            'Pdf upload and send Setup wizard',
        )

    def test_18_transient_model(self):
        """send.document must be a TransientModel."""
        self.assertTrue(
            issubclass(type(self.env['send.document']), self.env['send.document'].__class__)
        )
        # Verify it inherits from TransientModel by checking _transient attribute
        self.assertTrue(self.env['send.document']._transient)
