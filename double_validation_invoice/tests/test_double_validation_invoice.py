# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError


class TestDoubleValidationInvoice(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        # Create partner for invoice
        cls.partner = cls.env['res.partner'].create({
            'name': 'Double Validation Test Partner',
        })

        # Find sale journal
        cls.journal = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', cls.company.id)
        ], limit=1)
        if not cls.journal:
            cls.journal = cls.env['account.journal'].create({
                'name': 'Customer Invoices Test',
                'type': 'sale',
                'code': 'TINV',
                'company_id': cls.company.id,
            })

        # Find or create account for invoice lines
        cls.account = cls.env['account.account'].search([
            ('account_type', 'in', ('income', 'income_other'))
        ], limit=1)
        if not cls.account:
            cls.account = cls.env['account.account'].search([], limit=1)

        # Save original system parameters to restore them if needed
        cls.config_param_obj = cls.env['ir.config_parameter'].sudo()

    def _create_draft_invoice(self, amount):
        """Helper to create a draft customer invoice with a specific unit price."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'Consultancy Services',
                    'quantity': 1,
                    'price_unit': amount,
                    'account_id': self.account.id,
                })
            ]
        })
        return invoice

    def test_01_config_settings_read_write(self):
        """Test res.config.settings successfully writes parameters to system parameters."""
        config_wizard = self.env['res.config.settings'].create({
            'double_validation': True,
            'first_valid_limit': 1500,
            'second_valid_limit': 4500,
        })
        config_wizard.execute()

        # Verify values are correctly set in ir.config_parameter
        double_validation = self.config_param_obj.get_param('double_validation_invoice.double_validation')
        first_limit = self.config_param_obj.get_param('double_validation_invoice.first_valid_limit')
        second_limit = self.config_param_obj.get_param('double_validation_invoice.second_valid_limit')

        self.assertEqual(double_validation, 'True')
        self.assertEqual(first_limit, '1500')
        self.assertEqual(second_limit, '4500')

    def test_02_disabled_double_validation(self):
        """Test that invoices bypass validation approvals when double_validation is disabled."""
        self.config_param_obj.set_param('double_validation_invoice.double_validation', False)
        self.config_param_obj.set_param('double_validation_invoice.first_valid_limit', 1000)

        # Create draft invoice with amount 5000.0 (greater than first limit)
        invoice = self._create_draft_invoice(5000.0)
        self.assertEqual(invoice.state, 'draft')

        # Post the invoice
        invoice.action_post()

        # Assert invoice is directly posted
        self.assertEqual(invoice.state, 'posted')

    def test_03_under_first_limit_direct_post(self):
        """Test that invoices under or equal to the first limit are posted directly."""
        self.config_param_obj.set_param('double_validation_invoice.double_validation', True)
        self.config_param_obj.set_param('double_validation_invoice.first_valid_limit', 2000)

        # Create draft invoice with amount 1500.0 (under the limit of 2000)
        invoice = self._create_draft_invoice(1500.0)
        self.assertEqual(invoice.state, 'draft')

        # Post invoice
        invoice.action_post()

        # Assert invoice is directly posted
        self.assertEqual(invoice.state, 'posted')

    def test_04_first_stage_approval_only(self):
        """Test that invoices exceeding the first limit but under the second limit require first stage approval only."""
        self.config_param_obj.set_param('double_validation_invoice.double_validation', True)
        self.config_param_obj.set_param('double_validation_invoice.first_valid_limit', 1000)
        self.config_param_obj.set_param('double_validation_invoice.second_valid_limit', 3000)

        # Create draft invoice with amount 2500.0 (between 1000 and 3000)
        invoice = self._create_draft_invoice(2500.0)
        self.assertEqual(invoice.state, 'draft')

        # Post invoice
        invoice.action_post()

        # Assert state transitioned to 'first_approval'
        self.assertEqual(invoice.state, 'first_approval')

        # Approve first stage
        invoice.action_first_approval()

        # Assert invoice is posted directly (since amount 2500 <= second limit 3000)
        self.assertEqual(invoice.state, 'posted')

    def test_05_two_stage_approval(self):
        """Test that invoices exceeding the second limit require both first and second stage approvals."""
        self.config_param_obj.set_param('double_validation_invoice.double_validation', True)
        self.config_param_obj.set_param('double_validation_invoice.first_valid_limit', 1000)
        self.config_param_obj.set_param('double_validation_invoice.second_valid_limit', 3000)

        # Create draft invoice with amount 5000.0 (greater than second limit 3000)
        invoice = self._create_draft_invoice(5000.0)
        self.assertEqual(invoice.state, 'draft')

        # Post invoice
        invoice.action_post()

        # Assert state transitioned to 'first_approval'
        self.assertEqual(invoice.state, 'first_approval')

        # Approve first stage
        invoice.action_first_approval()

        # Assert state transitioned to 'second_approval' (since amount 5000 > second limit 3000)
        self.assertEqual(invoice.state, 'second_approval')

        # Approve second stage
        invoice.action_second_approval()

        # Assert invoice is posted
        self.assertEqual(invoice.state, 'posted')
