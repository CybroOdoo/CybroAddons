# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import logging

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import tagged, TransactionCase

try:
    import openpyxl
except ImportError:
    openpyxl = None

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_compliance', 'wm_reporting')
class TestWmComplianceReportBuilder(TransactionCase):
    """Unit tests verifying PDF and XLSX report generation in the Compliance Report Builder."""

    def setUp(self):
        """Set up test fixtures including generator, transporter, and facility."""
        super(TestWmComplianceReportBuilder, self).setUp()
        self.generator = self.env['res.partner'].create({
            'name': 'Report Builder Generator',
            'is_generator': True,
        })
        self.transporter = self.env['res.partner'].create({
            'name': 'Report Builder Transporter',
            'is_transporter': True,
        })
        self.facility = self.env['wm.disposal.facility'].create({
            'name': 'Report Builder Facility',
            'facility_type': 'recycling',
            'license_no': 'LIC-REP-2026',
        })
        self.category = self.env['wm.waste.category'].create({
            'name': 'Report Waste Category',
            'code': 'REP_CAT_01',
        })

        # Create 2 Manifests
        self.manifest1 = self.env['wm.compliance.manifest'].create({
            'name': 'MNF-REP-001',
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
            'manifest_date': fields.Date.today(),
            'state': 'submitted',
            'line_ids': [(0, 0, {
                'waste_category_id': self.category.id,
                'quantity': 150.0,
            })]
        })

        self.manifest2 = self.env['wm.compliance.manifest'].create({
            'name': 'MNF-REP-002',
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
            'manifest_date': fields.Date.today(),
            'state': 'collected',
            'line_ids': [(0, 0, {
                'waste_category_id': self.category.id,
                'quantity': 250.0,
            })]
        })

        # Create 2 Certificates
        self.cert1 = self.env['wm.compliance.certificate'].create({
            'name': 'CERT-REP-001',
            'certificate_no': 'CRT-001',
            'certificate_type': 'recycling',
            'facility_id': self.facility.id,
            'quantity': 150.0,
            'manifest_id': self.manifest1.id,
            'issued_date': fields.Date.today(),
            'state': 'issued',
        })

        self.cert2 = self.env['wm.compliance.certificate'].create({
            'name': 'CERT-REP-002',
            'certificate_no': 'CRT-002',
            'certificate_type': 'disposal',
            'facility_id': self.facility.id,
            'quantity': 250.0,
            'manifest_id': self.manifest2.id,
            'issued_date': fields.Date.today(),
            'state': 'draft',
        })

    def test_single_manifest_pdf_report(self):
        """Test generating single manifest PDF report via report builder."""
        wizard = self.env['wm.compliance.report'].create({
            'report_type': 'manifest',
            'output_format': 'pdf',
            'date_from': fields.Date.today(),
            'date_to': fields.Date.today(),
            'facility_id': self.facility.id,
        })
        self.manifest2.unlink()
        res = wizard.action_generate()
        self.assertEqual(res.get('type'), 'ir.actions.report')
        self.assertEqual(res.get('report_name'), 'wm_compliance.report_compliance_manifest_template')
        _logger.info('PASS: test_single_manifest_pdf_report')

    def test_multi_manifest_pdf_report(self):
        """Test generating multiple manifests PDF report via report builder."""
        wizard = self.env['wm.compliance.report'].create({
            'report_type': 'manifest',
            'output_format': 'pdf',
            'date_from': fields.Date.today(),
            'date_to': fields.Date.today(),
            'facility_id': self.facility.id,
        })
        res = wizard.action_generate()
        self.assertEqual(res.get('type'), 'ir.actions.report')
        self.assertEqual(res.get('report_name'), 'wm_compliance.report_compliance_manifest_template')
        self.assertEqual(len(res.get('context', {}).get('active_ids', [])), 2)
        report = self.env.ref('wm_compliance.action_report_compliance_manifest')
        pdf_bytes, _ = report._render_qweb_pdf(report.id, res['context']['active_ids'])
        self.assertTrue(len(pdf_bytes) > 0, "PDF content must be non-empty")
        _logger.info('PASS: test_multi_manifest_pdf_report')

    def test_single_certificate_pdf_report(self):
        """Test generating single certificate PDF report via report builder."""
        wizard = self.env['wm.compliance.report'].create({
            'report_type': 'certificate',
            'output_format': 'pdf',
            'date_from': fields.Date.today(),
            'date_to': fields.Date.today(),
            'facility_id': self.facility.id,
        })
        self.cert2.unlink()
        res = wizard.action_generate()
        self.assertEqual(res.get('type'), 'ir.actions.report')
        self.assertEqual(res.get('report_name'), 'wm_compliance.report_compliance_certificate_template')
        report = self.env.ref('wm_compliance.action_report_compliance_certificate')
        pdf_bytes, _ = report._render_qweb_pdf(report.id, res['context']['active_ids'])
        self.assertTrue(len(pdf_bytes) > 0, "PDF content must be non-empty")
        _logger.info('PASS: test_single_certificate_pdf_report')

    def test_multi_certificate_pdf_report(self):
        """Test generating multiple certificates PDF report via report builder."""
        wizard = self.env['wm.compliance.report'].create({
            'report_type': 'certificate',
            'output_format': 'pdf',
            'date_from': fields.Date.today(),
            'date_to': fields.Date.today(),
            'facility_id': self.facility.id,
        })
        res = wizard.action_generate()
        self.assertEqual(res.get('type'), 'ir.actions.report')
        self.assertEqual(res.get('report_name'), 'wm_compliance.report_compliance_certificate_template')
        self.assertEqual(len(res.get('context', {}).get('active_ids', [])), 2)
        report = self.env.ref('wm_compliance.action_report_compliance_certificate')
        pdf_bytes, _ = report._render_qweb_pdf(report.id, res['context']['active_ids'])
        self.assertTrue(len(pdf_bytes) > 0, "PDF content must be non-empty")
        _logger.info('PASS: test_multi_certificate_pdf_report')

    def test_manifest_xlsx_report(self):
        """Test generating manifests XLSX report via report builder."""
        if not openpyxl:
            self.skipTest("openpyxl not available")
        wizard = self.env['wm.compliance.report'].create({
            'report_type': 'manifest',
            'output_format': 'xlsx',
            'date_from': fields.Date.today(),
            'date_to': fields.Date.today(),
            'facility_id': self.facility.id,
        })
        res = wizard.action_generate()
        self.assertEqual(res.get('type'), 'ir.actions.act_url')
        att_id = int(res['url'].split('/web/content/')[1].split('?')[0])
        att = self.env['ir.attachment'].browse(att_id)
        self.assertTrue(att.datas, "XLSX attachment data must be present")
        self.assertEqual(att.mimetype, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        _logger.info('PASS: test_manifest_xlsx_report')

    def test_certificate_xlsx_report(self):
        """Test generating certificates XLSX report via report builder."""
        if not openpyxl:
            self.skipTest("openpyxl not available")
        wizard = self.env['wm.compliance.report'].create({
            'report_type': 'certificate',
            'output_format': 'xlsx',
            'date_from': fields.Date.today(),
            'date_to': fields.Date.today(),
            'facility_id': self.facility.id,
        })
        res = wizard.action_generate()
        self.assertEqual(res.get('type'), 'ir.actions.act_url')
        att_id = int(res['url'].split('/web/content/')[1].split('?')[0])
        att = self.env['ir.attachment'].browse(att_id)
        self.assertTrue(att.datas, "XLSX attachment data must be present")
        self.assertEqual(att.mimetype, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        _logger.info('PASS: test_certificate_xlsx_report')

    def test_report_builder_validations(self):
        """Test date range constraint and empty criteria handling."""
        with self.assertRaises(ValidationError):
            self.env['wm.compliance.report'].create({
                'report_type': 'manifest',
                'date_from': fields.Date.from_string('2026-12-31'),
                'date_to': fields.Date.from_string('2026-01-01'),
            })

        empty_wizard = self.env['wm.compliance.report'].create({
            'report_type': 'manifest',
            'date_from': fields.Date.from_string('2020-01-01'),
            'date_to': fields.Date.from_string('2020-01-02'),
        })
        with self.assertRaises(UserError):
            empty_wizard.action_generate()
        _logger.info('PASS: test_report_builder_validations')

    def test_direct_qweb_report_rendering(self):
        """Test that QWeb report actions render templates without crash."""
        manifest_report = self.env.ref('wm_compliance.action_report_compliance_manifest')
        html_content, _ = manifest_report._render_qweb_html(manifest_report, [self.manifest1.id, self.manifest2.id])
        self.assertTrue(html_content)

        cert_report = self.env.ref('wm_compliance.action_report_compliance_certificate')
        html_content, _ = cert_report._render_qweb_html(cert_report, [self.cert1.id, self.cert2.id])
        self.assertTrue(html_content)
        _logger.info('PASS: test_direct_qweb_report_rendering')
