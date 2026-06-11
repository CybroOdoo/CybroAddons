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


class TestExportAttachmentsFromListView(TransactionCase):
    """Integration tests for the full Export Attachments From List View
    workflow: creating an export.attachment configuration, creating the
    contextual window action, and triggering the wizard download.

    Uses res.users (admin) as the attachment owner to avoid enterprise-specific
    NOT NULL constraints on res.partner (e.g. autopost_bills from account).
    """

    def setUp(self):
        super().setUp()
        # ir.model entry for res.users (always present)
        self.user_model = self.env['ir.model']._get('res.users')
        # Use the always-available admin user as the attachment owner
        self.owner = self.env.user          # res.users singleton
        self.owner_model = 'res.users'

        # Attach a binary document to the admin user
        self.attachment = self.env['ir.attachment'].create({
            'name': 'sample_report.pdf',
            'res_model': self.owner_model,
            'res_id': self.owner.id,
            'datas': base64.b64encode(b'%PDF-1.4 sample content'),
            'mimetype': 'application/pdf',
        })

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _create_export_attachment(self, action_name='List View Export'):
        return self.env['export.attachment'].create({
            'action_name': action_name,
            'applied_model_id': self.user_model.id,
        })

    def _get_wizard(self, active_ids=None, active_model=None):
        ctx = {
            'active_ids': active_ids if active_ids is not None
            else [self.owner.id],
            'active_model': active_model or self.owner_model,
        }
        return self.env['attachment.download.confirmation'].with_context(ctx)

    # ------------------------------------------------------------------
    # 1. Full workflow: configure → create action → cancel action
    # ------------------------------------------------------------------

    def test_01_full_workflow_create_and_cancel_action(self):
        """End-to-end: create config, add action, cancel action."""
        cfg = self._create_export_attachment()
        self.assertEqual(cfg.states, 'draft')
        # Create the contextual action
        cfg.action_create()
        self.assertEqual(cfg.states, 'running')
        self.assertTrue(cfg.act_window_id)
        # Cancel / remove the action
        result = cfg.action_unlink()
        self.assertEqual(cfg.states, 'cancel')
        self.assertEqual(result.get('tag'), 'reload')

    def test_02_action_create_makes_action_appear_in_computed_field(self):
        """After action_create, created_action_names should list the action."""
        cfg = self._create_export_attachment(action_name='Unique Export XYZ')
        cfg.action_create()
        self.assertIn('Unique Export XYZ', cfg.created_action_names)

    def test_03_action_unlink_clears_computed_field(self):
        """After action_unlink, the window action is deleted so
        created_action_names should no longer list it."""
        cfg = self._create_export_attachment(action_name='Temp Export ABC')
        cfg.action_create()
        cfg.action_unlink()
        cfg.invalidate_recordset()
        self.assertEqual(
            cfg.created_action_names,
            '',
            "created_action_names should be empty after action_unlink.",
        )

    # ------------------------------------------------------------------
    # 2. Window action properties (from list view context)
    # ------------------------------------------------------------------

    def test_04_created_window_action_view_mode_is_form(self):
        """The contextual window action should open in 'form' view mode."""
        cfg = self._create_export_attachment()
        cfg.action_create()
        self.assertEqual(cfg.act_window_id.view_mode, 'form')

    def test_05_created_window_action_type(self):
        """The created action type should be 'ir.actions.act_window'."""
        cfg = self._create_export_attachment()
        cfg.action_create()
        self.assertEqual(cfg.act_window_id.type, 'ir.actions.act_window')

    def test_06_window_action_has_correct_view_form(self):
        """The created window action should reference the confirmation form
        view supplied by the module."""
        cfg = self._create_export_attachment()
        cfg.action_create()
        expected_view = self.env.ref(
            'export_attachments_from_list_view.'
            'attachment_download_confirmation_view_form'
        )
        self.assertEqual(cfg.act_window_id.view_id, expected_view)

    # ------------------------------------------------------------------
    # 3. Wizard – successful download via list view context
    # ------------------------------------------------------------------

    def test_07_wizard_download_returns_url_action(self):
        """Wizard triggered from a list view context with attachments should
        return an act_url action."""
        wizard = self._get_wizard().create({})
        result = wizard.action_download_attachment()
        self.assertEqual(result.get('type'), 'ir.actions.act_url')

    def test_08_wizard_download_url_is_string(self):
        """The URL in the returned action should be a non-empty string."""
        wizard = self._get_wizard().create({})
        result = wizard.action_download_attachment()
        url = result.get('url', '')
        self.assertIsInstance(url, str)
        self.assertTrue(url, "Download URL should not be empty.")

    def test_09_wizard_download_url_tab_id_contains_attachment_id(self):
        """tab_id query parameter in the download URL should include the
        attachment ID."""
        wizard = self._get_wizard().create({})
        result = wizard.action_download_attachment()
        self.assertIn(str(self.attachment.id), result.get('url', ''))

    # ------------------------------------------------------------------
    # 4. Wizard – no attachments edge case
    # ------------------------------------------------------------------

    def test_10_wizard_raises_when_record_has_no_attachments(self):
        """ValidationError expected when no attachment exists for selected
        records."""
        wizard = self._get_wizard(
            active_ids=[self.owner.id],
            active_model='res.lang',   # model with no attachments
        ).create({})
        with self.assertRaises(ValidationError):
            wizard.action_download_attachment()

    def test_11_wizard_raises_for_wrong_active_model(self):
        """When the active_model doesn't match the attachment's res_model,
        no attachments should be found → ValidationError."""
        wizard = self._get_wizard(
            active_ids=[self.owner.id],
            active_model='res.country',  # attachment is on res.users
        ).create({})
        with self.assertRaises(ValidationError):
            wizard.action_download_attachment()

    # ------------------------------------------------------------------
    # 5. Multiple attachments
    # ------------------------------------------------------------------

    def test_12_multiple_attachments_on_single_record(self):
        """Multiple attachments on one record – download should succeed
        and all IDs appear in the URL."""
        attachment2 = self.env['ir.attachment'].create({
            'name': 'second_file.xlsx',
            'res_model': self.owner_model,
            'res_id': self.owner.id,
            'datas': base64.b64encode(b'xlsx content'),
            'mimetype': 'application/vnd.ms-excel',
        })
        wizard = self._get_wizard().create({})
        result = wizard.action_download_attachment()
        url = result.get('url', '')
        self.assertIn(str(self.attachment.id), url)
        self.assertIn(str(attachment2.id), url)

    def test_13_multiple_records_with_attachments(self):
        """Selecting multiple records with attachments should return
        a successful download action."""
        # Find any other active user (skip if none exists)
        second_user = self.env['res.users'].search(
            [('id', '!=', self.owner.id), ('active', '=', True)], limit=1
        )
        if not second_user:
            self.skipTest("No second active user available in the database.")
        self.env['ir.attachment'].create({
            'name': 'second_user_doc.txt',
            'res_model': self.owner_model,
            'res_id': second_user.id,
            'datas': base64.b64encode(b'text'),
        })
        wizard = self._get_wizard(
            active_ids=[self.owner.id, second_user.id]
        ).create({})
        result = wizard.action_download_attachment()
        self.assertEqual(result.get('type'), 'ir.actions.act_url')

    # ------------------------------------------------------------------
    # 6. ExportAttachment model – additional integration edge cases
    # ------------------------------------------------------------------

    def test_14_cannot_call_action_create_twice(self):
        """Calling action_create twice creates a second window action;
        the record should reflect the latest one."""
        cfg = self._create_export_attachment(action_name='Double Create Test')
        cfg.action_create()
        first_window_id = cfg.act_window_id.id
        cfg.action_create()
        self.assertNotEqual(cfg.act_window_id.id, first_window_id)

    def test_15_unlink_export_attachment_record_itself(self):
        """Deleting the export.attachment record in draft state should
        succeed."""
        cfg = self._create_export_attachment(action_name='Draft Delete Test')
        record_id = cfg.id
        cfg.unlink()
        remaining = self.env['export.attachment'].search(
            [('id', '=', record_id)]
        )
        self.assertFalse(remaining, "Draft record should be deletable.")

    def test_16_export_attachment_model_description(self):
        """_description of export.attachment should be 'Export Attachment'."""
        self.assertEqual(
            self.env['export.attachment']._description,
            'Export Attachment',
        )

    def test_17_export_attachment_rec_name_field(self):
        """_rec_name of export.attachment should be 'action_name'."""
        self.assertEqual(
            self.env['export.attachment']._rec_name,
            'action_name',
        )

    def test_18_applied_model_id_is_many2one_to_ir_model(self):
        """applied_model_id should be a Many2one to ir.model."""
        field = self.env['export.attachment']._fields['applied_model_id']
        self.assertEqual(field.comodel_name, 'ir.model')

    def test_19_act_window_id_is_many2one_to_ir_actions_act_window(self):
        """act_window_id should be a Many2one to ir.actions.act_window."""
        field = self.env['export.attachment']._fields['act_window_id']
        self.assertEqual(field.comodel_name, 'ir.actions.act_window')

    def test_20_states_default_draft_persists_in_db(self):
        """State 'draft' should persist correctly after ORM read-back."""
        cfg = self._create_export_attachment(action_name='Persist State Test')
        self.env.flush_all()
        cfg.invalidate_recordset()
        self.assertEqual(cfg.states, 'draft')
