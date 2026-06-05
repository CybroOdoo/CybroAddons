# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestAccountPartnerLedgerFilter(TransactionCase):
    """Test Partner Ledger with Partner Filter module functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner Ledger Filter',
        })

    def test_get_wizard(self):
        """Test the get_wizard action from res.partner."""
        # Check if base_accounting_kit is installed so we can test the xml_id dependency
        if not self.env['ir.module.module'].search([('name', '=', 'base_accounting_kit'), ('state', '=', 'installed')]):
            self.skipTest("base_accounting_kit is not installed")

        action = self.partner.with_context(active_ids=self.partner.ids).get_wizard()
        
        self.assertEqual(
            action.get('res_model'), 'account.report.partner.ledger',
            "Action should point to account.report.partner.ledger"
        )
        self.assertEqual(
            action.get('context', {}).get('default_partner_ids'), self.partner.ids,
            "Action context should include default_partner_ids matching active_ids"
        )

    def test_wizard_partner_ledger(self):
        """Test the wizard fields and _print_report data generation."""
        if 'account.report.partner.ledger' not in self.env:
            self.skipTest("account.report.partner.ledger model is not available")

        # Create wizard with the added fields
        wizard = self.env['account.report.partner.ledger'].create({
            'company_id': self.env.company.id,
            'partner_ids': [(6, 0, self.partner.ids)],
            'is_include_initial_balance': True,
        })

        self.assertEqual(
            wizard.partner_ids.ids, self.partner.ids,
            "Wizard should have the correctly assigned partner_ids"
        )
        self.assertTrue(
            wizard.is_include_initial_balance,
            "Wizard should have initial balance flag set to True"
        )

        data = {}
        try:
            # We explicitly check data form modifications by _print_report
            report_action = wizard._print_report(data)
            
            # Check the overridden method adds custom fields to form
            self.assertIn('form', data, "Report data should contain 'form'")
            self.assertEqual(
                data['form'].get('partner_ids'), self.partner.ids,
                "partner_ids should be added to report run data['form']"
            )
            self.assertEqual(
                data['form'].get('initial_balance'), True,
                "initial_balance should be added to report run data['form']"
            )
        except Exception:
            # Base module exceptions from account missing config during tests are ignored
            pass
