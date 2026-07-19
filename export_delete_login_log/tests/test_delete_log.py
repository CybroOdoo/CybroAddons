# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo.tests.common import TransactionCase



class TestDeleteLog(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestDeleteLog, cls).setUpClass()

        # 1. Fetch the 'res.partner' ir.model record to use for tracking configuration
        cls.partner_model = cls.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        cls.company_model = cls.env['ir.model'].search([('model', '=', 'res.company')], limit=1)

        # 2. Create some dummy records to test deletion
        cls.partner_1 = cls.env['res.partner'].create({'name': 'Test Partner One'})
        cls.partner_2 = cls.env['res.partner'].create({'name': 'Test Partner Two'})
        cls.company_1 = cls.env['res.company'].create({'name': 'Test Company'})

        # System parameter key based on your code
        cls.param_key = 'export_delete_login_log.delete_log_models_ids'

    def test_01_no_log_created_when_parameter_missing(self):
        """Test that unlinking a record doesn't generate a log if the config parameter isn't set."""
        # Ensure the parameter is empty/removed
        self.env['ir.config_parameter'].sudo().set_param(self.param_key, False)

        partner_id = self.partner_1.id
        self.partner_1.unlink()

        # Check that no log was created for this record ID
        log = self.env['delete.log'].search([
            ('rec_model_id', '=', self.partner_model.id),
            ('rec_id', '=', str(partner_id))
        ])
        self.assertFalse(log, "A log was created even though tracking configuration was missing.")

    def test_02_log_created_for_tracked_model(self):
        """Test that unlinking a record in a tracked model successfully creates a delete log."""
        # Configure 'res.partner' ID into the system parameters list
        tracked_ids = str([self.partner_model.id])
        self.env['ir.config_parameter'].sudo().set_param(self.param_key, tracked_ids)

        partner_id = self.partner_2.id
        partner_name = self.partner_2.display_name

        # Perform deletion
        self.partner_2.unlink()

        # Verify log entry creation
        log = self.env['delete.log'].search([
            ('rec_model_id', '=', self.partner_model.id),
            ('rec_id', '=', str(partner_id))
        ])

        self.assertTrue(log, "Delete log was not created for the tracked model.")
        self.assertEqual(log.rec_name, partner_name, "The logged record name does not match.")
        self.assertEqual(log.user_id, self.env.user, "The user who deleted the record was not captured correctly.")

    def test_03_no_log_for_untracked_model(self):
        """Test that unlinking a record from an untracked model does NOT create a delete log."""
        # Only track 'res.partner'
        tracked_ids = str([self.partner_model.id])
        self.env['ir.config_parameter'].sudo().set_param(self.param_key, tracked_ids)

        company_id = self.company_1.id

        # Unlink a company record (not tracked)
        self.company_1.unlink()

        # Check that no log was created for the company
        log = self.env['delete.log'].search([
            ('rec_model_id', '=', self.company_model.id),
            ('rec_id', '=', str(company_id))
        ])
        self.assertFalse(log, "A delete log was incorrectly created for an untracked model.")

    def test_04_batch_deletion_logging(self):
        """Test that deleting records in a batch logs every individual record properly."""
        # Configure tracking
        tracked_ids = str([self.partner_model.id])
        self.env['ir.config_parameter'].sudo().set_param(self.param_key, tracked_ids)

        # Create multiple batch partners
        partners = self.env['res.partner'].create([
            {'name': 'Batch Partner A'},
            {'name': 'Batch Partner B'}
        ])
        partner_ids = [str(p.id) for p in partners]

        # Batch unlink
        partners.unlink()

        # Verify logs count matches the batch size
        logs = self.env['delete.log'].search([
            ('rec_model_id', '=', self.partner_model.id),
            ('rec_id', 'in', partner_ids)
        ])
        self.assertEqual(len(logs), 2, "Batch deletion did not log all records.")