# -*- coding: utf-8 -*-
################################################################################
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
################################################################################
from datetime import timedelta
from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestCertificateLicense(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a test customer/partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@example.com',
        })

        # Create a certificate type
        cls.cert_type = cls.env['certificate.type'].create({
            'certificate_type': 'ISO 9001',
        })

        # Create a license type
        cls.lic_type = cls.env['certificate.license.type'].create({
            'license_type': 'Commercial License',
        })

        # Create a certificate tag
        cls.cert_tag = cls.env['certificate.tag'].create({
            'certificates_tags': 'Important',
        })

        # Create a license tag
        cls.lic_tag = cls.env['certificate.license.tag'].create({
            'license_tag': 'Business',
        })

        # Create a project and task
        cls.project = cls.env['project.project'].create({
            'name': 'Test Project',
        })
        cls.task = cls.env['project.task'].create({
            'name': 'Test Task',
            'project_id': cls.project.id,
        })

        # Create a product
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
        })

        # Create a test company
        cls.test_company = cls.env['res.company'].create({
            'name': 'Test Issued Company',
        })

        # Create a responsible user
        cls.responsible_user = cls.env['res.users'].create({
            'name': 'Responsible User',
            'login': 'responsible_user_cert_lic',
            'email': 'responsible@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])]
        })

    def _create_certificate(self, vals=None):
        default_vals = {
            'name': 'Test Certificate',
            'customer_id': self.partner.id,
            'certificates_types_id': self.cert_type.id,
            'start_date': fields.Date.today(),
            'expire_date': fields.Date.today() + timedelta(days=10),
            'issued_company_id': self.test_company.id,
            'project_id': self.project.id,
            'task_id': self.task.id,
            'product_id': self.product.id,
            'user_id': self.responsible_user.id,
            'description': 'Test Certificate Description',
            'expire_remainder_day': 5,
        }
        if vals:
            default_vals.update(vals)
        return self.env['certificate.certificate'].create(default_vals)

    def _create_license(self, vals=None):
        default_vals = {
            'name': 'Test License',
            'customer_id': self.partner.id,
            'license_types_id': self.lic_type.id,
            'start_date': fields.Date.today(),
            'expire_date': fields.Date.today() + timedelta(days=10),
            'issued_company_id': self.test_company.id,
            'project_id': self.project.id,
            'task_id': self.task.id,
            'product_id': self.product.id,
            'user_id': self.responsible_user.id,
            'description': 'Test License Description',
            'expire_remainder_day': 5,
        }
        if vals:
            default_vals.update(vals)
        return self.env['certificate.license'].create(default_vals)

    def test_01_create_certificate_and_license(self):
        """Test default values, sequence generation, and tags on creation."""
        cert = self._create_certificate()
        self.assertEqual(cert.state, 'new', "Initial state should be 'new'")
        self.assertNotEqual(cert.certificate_number, 'New', "Sequence number should be generated")
        self.assertTrue(cert.certificate_number.startswith('CER'), "Certificate number should match sequence format starting with CER")

        lic = self._create_license()
        self.assertEqual(lic.state, 'new', "Initial state should be 'new'")
        self.assertNotEqual(lic.license_number, 'New', "Sequence number should be generated")
        self.assertTrue(lic.license_number.startswith('LIC'), "License number should match sequence format starting with LIC")

    def test_02_validation_constraints(self):
        """Test validation constraints on certificate and license dates."""
        today = fields.Date.today()
        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)

        # Case 1: start_date > expire_date
        with self.assertRaises(ValidationError, msg="Should raise ValidationError when start_date > expire_date"):
            self._create_certificate({'start_date': tomorrow, 'expire_date': today})

        with self.assertRaises(ValidationError, msg="Should raise ValidationError when start_date > expire_date"):
            self._create_license({'start_date': tomorrow, 'expire_date': today})

        # Case 2: today > expire_date (past expire date)
        with self.assertRaises(ValidationError, msg="Should raise ValidationError when expire_date is in the past"):
            self._create_certificate({'start_date': yesterday, 'expire_date': yesterday})

        with self.assertRaises(ValidationError, msg="Should raise ValidationError when expire_date is in the past"):
            self._create_license({'start_date': yesterday, 'expire_date': yesterday})

    def test_03_active_transitions(self):
        """Test active state transitions and window actions."""
        cert = self._create_certificate()
        self.assertEqual(cert.state, 'new')
        cert.active_certificate()
        self.assertEqual(cert.state, 'active')

        lic = self._create_license()
        self.assertEqual(lic.state, 'new')
        lic.active_license()
        self.assertEqual(lic.state, 'active')

        # Test the view actions
        cert_view_action = cert.action_view_active_certificates()
        self.assertEqual(cert_view_action['res_model'], 'certificate.certificate')
        self.assertEqual(cert_view_action['type'], 'ir.actions.act_window')
        self.assertEqual(cert_view_action['domain'], [('state', '=', 'active')])

        lic_view_action = lic.action_view_active_licenses()
        self.assertEqual(lic_view_action['res_model'], 'certificate.license')
        self.assertEqual(lic_view_action['type'], 'ir.actions.act_window')
        self.assertEqual(lic_view_action['domain'], [('state', '=', 'active')])

    def test_04_scheduler_expiry(self):
        """Test the scheduler actions for warning, expiration states, and edge cases."""
        # 1. Test "expired_soon" transition.
        cert_warning = self._create_certificate({
            'expire_date': fields.Date.today() + timedelta(days=1),
            'expire_remainder_day': 2,
        })
        self.env['certificate.certificate'].certificate_expiry_action()
        self.assertEqual(cert_warning.state, 'expired_soon', "Should change state to expired_soon")

        lic_warning = self._create_license({
            'expire_date': fields.Date.today() + timedelta(days=1),
            'expire_remainder_day': 2,
        })
        self.env['certificate.license'].license_expiry_action()
        self.assertEqual(lic_warning.state, 'expired_soon', "Should change state to expired_soon")

        # 2. Test "expired" transition.
        cert_expired = self._create_certificate({
            'expire_date': fields.Date.today(),
            'expire_remainder_day': 0,
        })
        initial_cert_mail_count = self.env['mail.mail'].search_count([
            ('model', '=', 'certificate.certificate'),
            ('res_id', '=', cert_expired.id),
        ])

        self.env['certificate.certificate'].certificate_expiry_action()
        self.assertEqual(cert_expired.state, 'expired', "State should change to expired")
        self.assertTrue(cert_expired.has_expired, "has_expired should be True")

        cert_mails = self.env['mail.mail'].search([
            ('model', '=', 'certificate.certificate'),
            ('res_id', '=', cert_expired.id),
        ])
        self.assertEqual(len(cert_mails), initial_cert_mail_count + 1, "Exactly one email should be queued")

        lic_expired = self._create_license({
            'expire_date': fields.Date.today(),
            'expire_remainder_day': 0,
        })
        initial_lic_mail_count = self.env['mail.mail'].search_count([
            ('model', '=', 'certificate.license'),
            ('res_id', '=', lic_expired.id),
        ])

        self.env['certificate.license'].license_expiry_action()
        self.assertEqual(lic_expired.state, 'expired', "State should change to expired")
        self.assertTrue(lic_expired.has_expired, "has_expired should be True")

        lic_mails = self.env['mail.mail'].search([
            ('model', '=', 'certificate.license'),
            ('res_id', '=', lic_expired.id),
        ])
        self.assertEqual(len(lic_mails), initial_lic_mail_count + 1, "Exactly one email should be queued")

        # 3. Test edge case: customer without email, cron re-runs, and record without expire_date
        partner_no_email = self.env['res.partner'].create({'name': 'No Email Partner'})
        cert_no_email = self._create_certificate({
            'customer_id': partner_no_email.id,
            'expire_date': fields.Date.today(),
            'expire_remainder_day': 0,
        })
        lic_no_email = self._create_license({
            'customer_id': partner_no_email.id,
            'expire_date': fields.Date.today(),
            'expire_remainder_day': 0,
        })
        # Re-run schedulers to verify idempotency and safe email handling
        self.env['certificate.certificate'].certificate_expiry_action()
        self.env['certificate.license'].license_expiry_action()
        self.assertEqual(cert_no_email.state, 'expired')
        self.assertEqual(lic_no_email.state, 'expired')

    def test_05_res_partner_computes_and_actions(self):
        """Test compute fields and window action methods on res.partner."""
        test_partner = self.env['res.partner'].create({
            'name': 'Partner with count test',
            'email': 'partner_count@example.com',
        })

        # Initially counts should be 0
        test_partner._compute_total_certificates_count()
        test_partner._compute_total_license_count()
        self.assertEqual(test_partner.certificate_count, 0)
        self.assertEqual(test_partner.license_count, 0)

        # Create one certificate and one license for this partner
        self._create_certificate({'customer_id': test_partner.id})
        self._create_license({'customer_id': test_partner.id})

        # Test multi-recordset compute
        partners = test_partner | self.partner
        partners.invalidate_recordset(['certificate_count', 'license_count'])
        partners._compute_total_certificates_count()
        partners._compute_total_license_count()
        self.assertGreaterEqual(test_partner.certificate_count, 1)
        # Test that an internal user with no certificate groups can access partner without AccessError
        partner_as_internal_user = test_partner.with_user(self.responsible_user)
        partner_as_internal_user.invalidate_recordset(['name', 'email'])
        read_res = partner_as_internal_user.read(['name', 'email'])
        self.assertEqual(read_res[0]['name'], test_partner.name)
        partner_as_internal_user._compute_total_certificates_count()
        partner_as_internal_user._compute_total_license_count()
        with self.assertRaises(AccessError):
            _ = partner_as_internal_user.certificate_count

        # Test action methods (both standard and backward-compatibility methods)
        cert_action = test_partner.action_show_certificates()
        self.assertEqual(cert_action['res_model'], 'certificate.certificate')
        self.assertEqual(cert_action['domain'], [('customer_id', '=', test_partner.id)])
        self.assertEqual(test_partner.show_certificates()['res_model'], 'certificate.certificate')

        lic_action = test_partner.action_show_license()
        self.assertEqual(lic_action['res_model'], 'certificate.license')
        self.assertEqual(lic_action['domain'], [('customer_id', '=', test_partner.id)])
        self.assertEqual(test_partner.show_license()['res_model'], 'certificate.license')

    def test_06_pdf_reports(self):
        """Test PDF report generation actions."""
        cert = self._create_certificate()
        cert_report_action = cert.with_context(discard_logo_check=True).action_create_certificate_pdf_report()
        self.assertEqual(cert_report_action['type'], 'ir.actions.report')
        self.assertEqual(cert_report_action['report_name'], 'certificate_license_expiry.report_certificates')

        lic = self._create_license()
        lic_report_action = lic.with_context(discard_logo_check=True).action_create_license_pdf_report()
        self.assertEqual(lic_report_action['type'], 'ir.actions.report')
        self.assertEqual(lic_report_action['report_name'], 'certificate_license_expiry.report_license')
