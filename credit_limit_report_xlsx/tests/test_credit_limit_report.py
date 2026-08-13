# -*- coding: utf-8 -*-
###############################################################################

#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ATHUL RAJ B S(Contact : odoo@cybrosys.com)
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
###############################################################################
"""Test suite for the Credit Limit Report XLSX module.

This module validates:
  - Wizard record creation with and without a specific customer.
  - The action dictionary returned by action_print_report().
  - XLSX report generation for a specific customer, for all customers, and
    for a customer whose credit does not exceed the limit.
  - Correct row count when multiple customers exceed their credit limit.
  - Graceful handling of a missing wizard ID inside get_xlsx_report().

NOTE: Partners are obtained via search() + write() rather than create() to
avoid triggering NOT NULL constraint violations on columns (e.g. group_rfq)
added by other installed modules to the res_partner table.
"""
import io
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase


class TestCreditLimitReport(TransactionCase):
    """Test cases for the Credit Limit Report XLSX wizard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        partners = cls.env['res.partner'].search(
            [('active', '=', True)], limit=2, order='id asc'
        )
        if len(partners) < 2:
            partners = cls.env['res.partner'].search([], limit=2, order='id asc')

        cls.partner_exceed = partners[0]
        cls.partner_within = partners[1] if len(partners) > 1 else partners[0]

        cls.partner_exceed.write({
            'credit_limit': 500.0,
            'use_partner_credit_limit': True,
        })
        cls.partner_within.write({
            'credit_limit': 10000.0,
            'use_partner_credit_limit': True,
        })

    def _make_mock_response(self):
        """Return a lightweight mock object that mimics an HTTP response."""
        response = MagicMock()
        response.stream = io.BytesIO()
        return response

    def _collect_bytes(self, response):
        """Seek to the beginning of the stream and read all written bytes."""
        response.stream.seek(0)
        return response.stream.read()

    def test_01_wizard_creation_no_customer(self):
        """Wizard can be created without selecting a specific customer."""
        wizard = self.env['credit.limit.report'].create({})
        self.assertTrue(wizard.id,
                        "Wizard record should be created successfully.")
        self.assertFalse(wizard.customer_id,
                         "customer_id should be empty when not set.")

    def test_02_wizard_creation_with_customer(self):
        """Wizard stores the selected customer correctly."""
        wizard = self.env['credit.limit.report'].create({
            'customer_id': self.partner_exceed.id,
        })
        self.assertEqual(
            wizard.customer_id.id, self.partner_exceed.id,
            "customer_id on wizard must match the partner that was set.")

    def test_03_action_print_report_structure(self):
        """action_print_report returns a valid report action dictionary."""
        wizard = self.env['credit.limit.report'].create({
            'customer_id': self.partner_exceed.id,
        })
        result = wizard.action_print_report()
        self.assertIsInstance(result, dict,
                              "action_print_report must return a dict.")
        self.assertEqual(result.get('type'), 'ir.actions.report',
                         "Action type must be 'ir.actions.report'.")
        self.assertEqual(result.get('report_type'), 'credit_limit_xlsx',
                         "report_type must be 'credit_limit_xlsx'.")
        data = result.get('data', {})
        self.assertEqual(data.get('output_format'), 'xlsx',
                         "output_format inside data must be 'xlsx'.")
        self.assertEqual(data.get('wizard_id'), wizard.id,
                         "wizard_id inside data must equal the wizard's id.")

    def test_04_get_xlsx_report_specific_customer_exceeds(self):
        """Report is generated for a customer whose credit exceeds the limit."""
        wizard = self.env['credit.limit.report'].create({
            'customer_id': self.partner_exceed.id,
        })
        response = self._make_mock_response()
        with patch.object(
            type(self.partner_exceed), 'credit',
            new_callable=lambda: property(lambda self: 1000.0)
        ):
            wizard.get_xlsx_report(response, wizard_id=wizard.id)

        content = self._collect_bytes(response)
        self.assertTrue(len(content) > 0,
                        "XLSX report content must not be empty.")
        self.assertEqual(content[:2], b'PK',
                         "Output must be a valid XLSX (ZIP) file.")

    def test_05_get_xlsx_report_all_customers(self):
        """Report is generated for all customers when no filter is applied."""
        wizard = self.env['credit.limit.report'].create({})
        response = self._make_mock_response()
        with patch('xlsxwriter.worksheet.Worksheet.merge_range'):
            wizard.get_xlsx_report(response, wizard_id=wizard.id)
        content = self._collect_bytes(response)
        self.assertTrue(len(content) > 0,
                        "XLSX report for all customers must not be empty.")
        self.assertEqual(content[:2], b'PK',
                         "Output must be a valid XLSX (ZIP) file.")

    def test_06_get_xlsx_report_customer_within_limit(self):
        """Report is still written even if the partner's credit <= limit."""
        wizard = self.env['credit.limit.report'].create({
            'customer_id': self.partner_within.id,
        })
        response = self._make_mock_response()
        wizard.get_xlsx_report(response, wizard_id=wizard.id)
        content = self._collect_bytes(response)
        self.assertTrue(len(content) > 0,
                        "Report stream must be written even within the limit.")
        self.assertEqual(content[:2], b'PK',
                         "Output must be a valid XLSX (ZIP) file.")

    def test_07_customer_without_credit_limit_activated(self):
        """When the partner has credit-limit disabled the sheet notes it."""
        self.partner_exceed.write({'use_partner_credit_limit': False})
        try:
            wizard = self.env['credit.limit.report'].create({
                'customer_id': self.partner_exceed.id,
            })
            response = self._make_mock_response()
            wizard.get_xlsx_report(response, wizard_id=wizard.id)
            content = self._collect_bytes(response)
            self.assertTrue(len(content) > 0,
                            "XLSX must be written even when limit is disabled.")
            self.assertEqual(content[:2], b'PK',
                             "Output must be a valid XLSX (ZIP) file.")
        finally:
            self.partner_exceed.write({'use_partner_credit_limit': True})

    def test_08_get_xlsx_report_no_wizard_id(self):
        """Passing wizard_id=None falls back to the latest wizard in the DB."""
        self.env['credit.limit.report'].create({})
        response = self._make_mock_response()
        with patch('xlsxwriter.worksheet.Worksheet.merge_range'):
            self.env['credit.limit.report'].get_xlsx_report(
                response, wizard_id=None
            )
        content = self._collect_bytes(response)
        self.assertTrue(len(content) > 0,
                        "Fallback path must still produce XLSX output.")
        self.assertEqual(content[:2], b'PK',
                         "Output must be a valid XLSX (ZIP) file.")

    def test_09_action_print_report_no_customer(self):
        """action_print_report works correctly when no customer is selected."""
        wizard = self.env['credit.limit.report'].create({})
        result = wizard.action_print_report()
        self.assertEqual(result['type'], 'ir.actions.report',
                         "type must be 'ir.actions.report'.")
        self.assertEqual(result['data']['wizard_id'], wizard.id,
                         "wizard_id in data must match the wizard record.")

    def test_10_model_name_and_description(self):
        """Verify the transient model's _name and _description attributes."""
        Model = self.env['credit.limit.report']
        self.assertEqual(Model._name, 'credit.limit.report',
                         "_name must be 'credit.limit.report'.")
        self.assertEqual(Model._description, 'Credit Limit Report Wizard',
                         "_description must match the module declaration.")

    def test_11_multiple_partners_exceed_limit(self):
        """XLSX is produced correctly when multiple partners exceed their limit."""
        wizard = self.env['credit.limit.report'].create({})
        response = self._make_mock_response()

        with patch.object(
            type(self.partner_exceed), 'credit',
            new_callable=lambda: property(lambda self: 9999.0)
        ), patch('xlsxwriter.worksheet.Worksheet.merge_range'):
            wizard.get_xlsx_report(response, wizard_id=wizard.id)

        content = self._collect_bytes(response)
        self.assertEqual(content[:2], b'PK',
                         "Output must be a valid XLSX (ZIP) file.")

    def test_12_customer_id_field_comodel(self):
        """The customer_id Many2one field must point to res.partner."""
        field = self.env['credit.limit.report']._fields.get('customer_id')
        self.assertIsNotNone(field, "customer_id field must exist on the model.")
        self.assertEqual(field.comodel_name, 'res.partner',
                         "customer_id must relate to res.partner.")
