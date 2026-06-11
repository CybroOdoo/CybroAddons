# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
import base64
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestAttachmentDownloadConfirmation(TransactionCase):
    """Test cases for the AttachmentDownloadConfirmation wizard
    (attachment.download.confirmation).

    We use res.users (the admin user) as the owning record to avoid any
    NOT NULL constraints that enterprise modules add to res.partner
    (e.g. autopost_bills from the account module).
    """

    def setUp(self):
        super().setUp()
        # Use the always-available admin user as the attachment owner –
        # no record creation required, no enterprise-specific constraints.
        self.owner = self.env.user        # res.users singleton
        self.owner_model = 'res.users'

        # Create an attachment linked to the admin user
        self.attachment = self.env['ir.attachment'].create({
            'name': 'test_document.pdf',
            'res_model': self.owner_model,
            'res_id': self.owner.id,
            'datas': base64.b64encode(b'Dummy PDF content'),
            'mimetype': 'application/pdf',
        })

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _get_wizard(self, active_ids=None, active_model=None):
        """Instantiate the wizard with a context that mimics a list view
        multi-selection action."""
        ctx = {
            'active_ids': active_ids if active_ids is not None
            else [self.owner.id],
            'active_model': active_model or self.owner_model,
        }
        return self.env['attachment.download.confirmation'].with_context(ctx)

    # ------------------------------------------------------------------
    # 1. Wizard instantiation
    # ------------------------------------------------------------------

    def test_01_wizard_can_be_created(self):
        """The transient wizard should be instantiable without errors."""
        wizard = self._get_wizard().create({})
        self.assertTrue(wizard.id, "Wizard record should have been created.")

    # ------------------------------------------------------------------
    # 2. action_download_attachment – attachments found
    # ------------------------------------------------------------------

    def test_02_download_returns_act_url_action(self):
        """action_download_attachment should return an act_url action dict
        when at least one attachment is found."""
        wizard = self._get_wizard().create({})
        result = wizard.action_download_attachment()
        self.assertEqual(
            result.get('type'),
            'ir.actions.act_url',
            "Return type should be 'ir.actions.act_url'.",
        )

    def test_03_download_url_contains_attachment_id(self):
        """The returned URL should contain the attachment ID."""
        wizard = self._get_wizard().create({})
        result = wizard.action_download_attachment()
        url = result.get('url', '')
        self.assertIn(
            str(self.attachment.id),
            url,
            "Download URL should contain the attachment ID.",
        )

    def test_04_download_url_uses_download_document_endpoint(self):
        """The returned URL should point to /web/binary/download_document."""
        wizard = self._get_wizard().create({})
        result = wizard.action_download_attachment()
        self.assertIn(
            '/web/binary/download_document',
            result.get('url', ''),
        )

    def test_05_download_target_is_new(self):
        """The action target should be 'new' to open in a new tab/window."""
        wizard = self._get_wizard().create({})
        result = wizard.action_download_attachment()
        self.assertEqual(result.get('target'), 'new')

    def test_06_download_close_flag_is_true(self):
        """The action should carry close=True so the dialog auto-closes."""
        wizard = self._get_wizard().create({})
        result = wizard.action_download_attachment()
        self.assertTrue(result.get('close'))

    # ------------------------------------------------------------------
    # 3. action_download_attachment – no attachments found
    # ------------------------------------------------------------------

    def test_07_no_attachments_raises_validation_error(self):
        """ValidationError should be raised when no attachments exist for the
        selected records."""
        # Use the admin user id but a model that has no attachment for it
        wizard = self._get_wizard(
            active_ids=[self.owner.id],
            active_model='res.lang',   # no attachment linked here
        ).create({})
        with self.assertRaises(ValidationError):
            wizard.action_download_attachment()

    def test_08_no_attachments_error_message(self):
        """The ValidationError message should mention 'No attachments found'."""
        wizard = self._get_wizard(
            active_ids=[self.owner.id],
            active_model='res.lang',
        ).create({})
        try:
            wizard.action_download_attachment()
            self.fail("Expected ValidationError was not raised.")
        except ValidationError as exc:
            self.assertIn(
                'No attachments found',
                str(exc),
                "Error message should mention 'No attachments found'.",
            )

    def test_09_empty_active_ids_raises_validation_error(self):
        """Passing an empty active_ids list should raise ValidationError
        (no records to search attachments for)."""
        wizard = self._get_wizard(active_ids=[]).create({})
        with self.assertRaises(ValidationError):
            wizard.action_download_attachment()

    # ------------------------------------------------------------------
    # 4. Context handling
    # ------------------------------------------------------------------

    def test_10_context_active_model_used_for_search(self):
        """The wizard should use active_model from context to filter
        attachments by res_model."""
        # An attachment on the correct model → should succeed
        wizard = self._get_wizard().create({})
        result = wizard.action_download_attachment()
        self.assertEqual(result.get('type'), 'ir.actions.act_url')

    def test_11_multiple_record_ids_in_context(self):
        """When multiple active_ids are provided, attachments for any of those
        records should be considered."""
        # Find any other active user (skip if none exists)
        second_user = self.env['res.users'].search(
            [('id', '!=', self.owner.id), ('active', '=', True)], limit=1
        )
        if not second_user:
            self.skipTest("No second active user available in the database.")
        self.env['ir.attachment'].create({
            'name': 'second_user_doc.pdf',
            'res_model': self.owner_model,
            'res_id': second_user.id,
            'datas': base64.b64encode(b'Content'),
            'mimetype': 'application/pdf',
        })
        wizard = self._get_wizard(
            active_ids=[self.owner.id, second_user.id]
        ).create({})
        result = wizard.action_download_attachment()
        self.assertEqual(result.get('type'), 'ir.actions.act_url')

    # ------------------------------------------------------------------
    # 5. Model metadata
    # ------------------------------------------------------------------

    def test_12_model_name(self):
        """The wizard model name should be 'attachment.download.confirmation'."""
        self.assertEqual(
            self.env['attachment.download.confirmation']._name,
            'attachment.download.confirmation',
        )

    def test_13_model_description(self):
        """The wizard _description should be 'Confirmation Popup'."""
        self.assertEqual(
            self.env['attachment.download.confirmation']._description,
            'Confirmation Popup',
        )

    def test_14_model_is_transient(self):
        """attachment.download.confirmation should be a TransientModel."""
        from odoo.models import TransientModel as OdooTransientModel
        self.assertIsInstance(
            self.env['attachment.download.confirmation'],
            OdooTransientModel,
        )
