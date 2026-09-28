# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.info)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import logging
from odoo.tests import common
from odoo.exceptions import ValidationError
from datetime import date, timedelta

_logger = logging.getLogger(__name__)


class TestReportPDF(common.TransactionCase):
    def setUp(self):
        super(TestReportPDF, self).setUp()
        self.env.company.external_report_layout_id = self.env.ref('web.external_layout_standard')
        self.report_pdf = self.env['report.pdf']
        self.res_partner_model = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        self.name_field = self.env['ir.model.fields'].search(
            [('model_id', '=', self.res_partner_model.id), ('name', '=', 'name')], limit=1)
        self.date_field = self.env['ir.model.fields'].search(
            [('model_id', '=', self.res_partner_model.id), ('name', '=', 'create_date')], limit=1)

    def test_01_create_report(self):
        """Test report creation with valid data"""
        _logger.info("Executing test_01_create_report")
        report = self.report_pdf.create({
            'name': 'Test Report',
            'model_id': self.res_partner_model.id,
            'fields_ids': [(0, 0, {
                'report_field_id': self.name_field.id
            })]
        })
        self.assertTrue(report.id, "Report should be created successfully")

    def test_02_date_validation(self):
        """Test date validation constraint"""
        _logger.info("Executing test_02_date_validation")
        with self.assertRaises(ValidationError):
            self.report_pdf.create({
                'name': 'Test Date Validation',
                'model_id': self.res_partner_model.id,
                'start_date': date.today(),
                'end_date': date.today() - timedelta(days=5),
                'date_field_id': self.date_field.id,
                'fields_ids': [(0, 0, {
                    'report_field_id': self.name_field.id
                })]
            })

    def test_03_fields_validation(self):
        """Test fields_ids required constraint"""
        _logger.info("Executing test_03_fields_validation")
        with self.assertRaises(ValidationError):
            self.report_pdf.create({
                'name': 'Test Fields Validation',
                'model_id': self.res_partner_model.id,
                'fields_ids': []
            })

    def test_04_action_create_model(self):
        """Test action button creation"""
        _logger.info("Executing test_04_action_create_model")
        report = self.report_pdf.create({
            'name': 'Test Action Create',
            'model_id': self.res_partner_model.id,
            'fields_ids': [(0, 0, {
                'report_field_id': self.name_field.id
            })]
        })
        report.action_create_model()
        self.assertTrue(report.is_action_button, "Action button should be True")
        self.assertTrue(report.action_id, "Action ref id should be set")
        self.assertEqual(report.action_id.binding_model_id.id, self.res_partner_model.id)

    def test_05_action_unlink_action(self):
        """Test unlinking the created action"""
        _logger.info("Executing test_05_action_unlink_action")
        report = self.report_pdf.create({
            'name': 'Test Action Unlink',
            'model_id': self.res_partner_model.id,
            'fields_ids': [(0, 0, {
                'report_field_id': self.name_field.id
            })]
        })
        report.action_create_model()
        created_action_id = report.action_id.id
        self.assertTrue(created_action_id)
        report.action_unlink_action()
        self.assertFalse(report.is_action_button)
        self.assertFalse(report.action_id)

        # Check if the action is actually deleted
        action = self.env['ir.actions.act_window'].search([('id', '=', created_action_id)])
        self.assertFalse(action, "Action should be deleted")

    def test_06_action_print_report(self):
        """Test print report action returns expected dictionary"""
        _logger.info("Executing test_06_action_print_report")
        report = self.report_pdf.create({
            'name': 'Test Print',
            'model_id': self.res_partner_model.id,
            'fields_ids': [(0, 0, {
                'report_field_id': self.name_field.id
            })]
        })
        report._onchange_fields_ids()  # To set field_order
        report = report.with_context(discard_logo_check=True)
        action = report.action_print_report()
        self.assertTrue(action, "Should return an action")
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertIn('data', action)
        self.assertEqual(action['data']['report_name'], 'Test Print')
        self.assertEqual(action['data']['model_name'], 'res.partner')

        