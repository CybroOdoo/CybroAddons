# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase


class TestResConfigSettings(TransactionCase):
    """Test cases for the res.config.settings model extension."""

    def setUp(self):
        super().setUp()
        self.config_model = self.env['res.config.settings']
        # Find a sale journal for testing
        self.journal = self.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', self.env.company.id)],
            limit=1
        )
        if not self.journal:
            self.skipTest("No sale journal found for testing, skipping.")

    def test_config_settings_has_invoice_journal_field(self):
        """Test that the invoice_journal_id field exists on res.config.settings."""
        config = self.config_model.create({})
        self.assertIn('invoice_journal_id', config._fields,
                      "invoice_journal_id field should exist on res.config.settings.")


    def test_set_and_get_invoice_journal(self):
        """Test saving and retrieving the workshop invoice journal via config."""
        config = self.config_model.create({
            'invoice_journal_id': self.journal.id,
        })
        config.execute()
        stored_param = self.env['ir.config_parameter'].sudo().get_param(
            'fleet_car_workshop.invoice_journal_type')
        self.assertEqual(int(stored_param), self.journal.id,
                         "Config parameter should store the correct journal ID.")


    def test_invoice_journal_defaults_to_none(self):
        """Test that invoice_journal_id is False when no journal is configured."""
        # Clear any previously set parameter
        self.env['ir.config_parameter'].sudo().set_param(
            'fleet_car_workshop.invoice_journal_type', False)
        config = self.config_model.create({})
        self.assertFalse(config.invoice_journal_id,
                         "invoice_journal_id should be False when no param is set.")


    def test_update_invoice_journal(self):
        """Test updating the journal in config settings."""
        # Set an initial journal
        config = self.config_model.create({
            'invoice_journal_id': self.journal.id,
        })
        config.execute()
        # Search for a different journal, or just test setting it to False
        new_journal = self.env['account.journal'].search(
            [('type', '=', 'sale'), ('id', '!=', self.journal.id)], limit=1)
        
        new_val = new_journal.id if new_journal else False

        config2 = self.config_model.create({
            'invoice_journal_id': new_val,
        })
        config2.execute()
        stored_param = self.env['ir.config_parameter'].sudo().get_param(
            'fleet_car_workshop.invoice_journal_type')
        
        expected = new_val if new_val else False
        actual = int(stored_param) if stored_param else False
        
        # If expected is False, actual will be False. If expected is an ID, actual will be the ID.
        self.assertEqual(actual, expected,
                         "Config parameter should be updated with the new journal ID or False.")

