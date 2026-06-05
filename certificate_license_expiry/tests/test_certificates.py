# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError
from odoo.fields import Date

class TestCertificates(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env
        
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'test@example.com'
        })
        
        cls.company = cls.env['res.company'].create({
            'name': 'Test Issued Company'
        })
        
        cls.cert_type = cls.env['certificates.types'].create({
            'certificate_type': 'Test Type'
        })
        
        cls.cert_tag = cls.env['certificates.tags'].create({
            'certificates_tags': 'Test Tag'
        })
        
        cls.project = cls.env['project.project'].create({
            'name': 'Test Project'
        })
        
        cls.task = cls.env['project.task'].create({
            'name': 'Test Task',
            'project_id': cls.project.id
        })
        
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product'
        })

    def test_01_create_certificate(self):
        """Test certificate creation and default state"""
        certificate = self.env['certificates'].create({
            'name': 'Test Certificate',
            'customer_id': self.partner.id,
            'certificates_types_id': self.cert_type.id,
            'issued_company_id': self.company.id,
            'project_id': self.project.id,
            'task_id': self.task.id,
            'product_id': self.product.id,
            'description': 'Test Description',
            'start_date': Date.today(),
            'expire_date': Date.add(Date.today(), days=10),
            'certificates_tags_ids': [(6, 0, [self.cert_tag.id])]
        })
        self.assertEqual(certificate.state, 'new')
        self.assertNotEqual(certificate.certificate_number, 'New')

    def test_02_certificate_date_validation(self):
        """Test validation for start date and expire date"""
        with self.assertRaises(ValidationError):
            self.env['certificates'].create({
                'name': 'Invalid Certificate',
                'customer_id': self.partner.id,
                'certificates_types_id': self.cert_type.id,
                'issued_company_id': self.company.id,
                'project_id': self.project.id,
                'task_id': self.task.id,
                'product_id': self.product.id,
                'description': 'Test Description',
                'start_date': Date.today(),
                'expire_date': Date.subtract(Date.today(), days=5),
            })

    def test_03_active_certificate(self):
        """Test activating a certificate"""
        certificate = self.env['certificates'].create({
            'name': 'Test Certificate to Active',
            'customer_id': self.partner.id,
            'certificates_types_id': self.cert_type.id,
            'issued_company_id': self.company.id,
            'project_id': self.project.id,
            'task_id': self.task.id,
            'product_id': self.product.id,
            'description': 'Test Description',
            'start_date': Date.today(),
            'expire_date': Date.add(Date.today(), days=10),
        })
        certificate.active_certificate()
        self.assertEqual(certificate.state, 'active')
        
        action = certificate.action_active_certificate()
        self.assertEqual(action['res_model'], 'certificates')
        self.assertEqual(action['domain'], [('state', '=', 'active')])

    def test_04_certificate_expiry_action(self):
        """Test the scheduled action for certificate expiry"""
        certificate = self.env['certificates'].create({
            'name': 'Test Certificate Expiring',
            'customer_id': self.partner.id,
            'certificates_types_id': self.cert_type.id,
            'issued_company_id': self.company.id,
            'project_id': self.project.id,
            'task_id': self.task.id,
            'product_id': self.product.id,
            'description': 'Test Description',
            'start_date': Date.subtract(Date.today(), days=10),
            'expire_date': Date.today(),
            'expire_remainder_day': 2,
        })
        
        # Avoid constrains by overriding using ORM sql update if necessary, or just rely on the scheduler logic
        # Actually constraints will block create if expire date < today, but if expire date == today, it should pass or fail?
        # If today > expire_date, it raises error. If today == expire_date, it passes.
        
        self.env['certificates'].certificate_expiry_action()
        self.assertTrue(certificate.has_expired)
        self.assertEqual(certificate.state, 'expired')

    def test_05_certificate_report(self):
        """Test PDF report action"""
        certificate = self.env['certificates'].create({
            'name': 'Test Certificate Report',
            'customer_id': self.partner.id,
            'certificates_types_id': self.cert_type.id,
            'issued_company_id': self.company.id,
            'project_id': self.project.id,
            'task_id': self.task.id,
            'product_id': self.product.id,
            'description': 'Test Description',
            'start_date': Date.today(),
            'expire_date': Date.add(Date.today(), days=10),
        })
        action = certificate.action_create_certificate_pdf_report()
        self.assertEqual(action['type'], 'ir.actions.report')

    def test_06_partner_certificate_count(self):
        """Test res.partner certificate count and smart button"""
        self.env['certificates'].create({
            'name': 'Test Certificate 1',
            'customer_id': self.partner.id,
            'certificates_types_id': self.cert_type.id,
            'issued_company_id': self.company.id,
            'project_id': self.project.id,
            'task_id': self.task.id,
            'product_id': self.product.id,
            'description': 'Test Description',
            'start_date': Date.today(),
            'expire_date': Date.add(Date.today(), days=10),
        })
        self.partner._compute_total_certificates_count()
        self.assertEqual(self.partner.certificate_count, 1)
        
        action = self.partner.show_certificates()
        self.assertEqual(action['res_model'], 'certificates')
        self.assertEqual(action['domain'], [('customer_id', '=', self.partner.id)])
