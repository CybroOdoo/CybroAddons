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

class TestLicense(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env
        
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer for License',
            'email': 'test_license@example.com'
        })
        
        cls.company = cls.env['res.company'].create({
            'name': 'Test License Issued Company'
        })
        
        cls.license_type = cls.env['license.types'].create({
            'license_type': 'Test License Type'
        })
        
        cls.license_tag = cls.env['license.tags'].create({
            'license_tags_ids': 'Test License Tag'
        })
        
        cls.project = cls.env['project.project'].create({
            'name': 'Test License Project'
        })
        
        cls.task = cls.env['project.task'].create({
            'name': 'Test License Task',
            'project_id': cls.project.id
        })
        
        cls.product = cls.env['product.product'].create({
            'name': 'Test License Product'
        })

    def test_01_create_license(self):
        """Test license creation and default state"""
        license_rec = self.env['license'].create({
            'name': 'Test License',
            'customer_id': self.partner.id,
            'license_types_id': self.license_type.id,
            'issued_company_id': self.company.id,
            'project_id': self.project.id,
            'task_id': self.task.id,
            'product_id': self.product.id,
            'description': 'Test License Description',
            'start_date': Date.today(),
            'expire_date': Date.add(Date.today(), days=10),
            'license_tags_ids': [(6, 0, [self.license_tag.id])]
        })
        self.assertEqual(license_rec.state, 'new')
        self.assertNotEqual(license_rec.license_number, 'New')

    def test_02_license_date_validation(self):
        """Test validation for start date and expire date"""
        with self.assertRaises(ValidationError):
            self.env['license'].create({
                'name': 'Invalid License',
                'customer_id': self.partner.id,
                'license_types_id': self.license_type.id,
                'issued_company_id': self.company.id,
                'project_id': self.project.id,
                'task_id': self.task.id,
                'product_id': self.product.id,
                'description': 'Test License Description',
                'start_date': Date.today(),
                'expire_date': Date.subtract(Date.today(), days=5),
            })

    def test_03_active_license(self):
        """Test activating a license"""
        license_rec = self.env['license'].create({
            'name': 'Test License to Active',
            'customer_id': self.partner.id,
            'license_types_id': self.license_type.id,
            'issued_company_id': self.company.id,
            'project_id': self.project.id,
            'task_id': self.task.id,
            'product_id': self.product.id,
            'description': 'Test License Description',
            'start_date': Date.today(),
            'expire_date': Date.add(Date.today(), days=10),
        })
        license_rec.active_license()
        self.assertEqual(license_rec.state, 'active')
        
        action = license_rec.action_active_license()
        self.assertEqual(action['res_model'], 'license')
        self.assertEqual(action['domain'], [('state', '=', 'active')])

    def test_04_license_expiry_action(self):
        """Test the scheduled action for license expiry"""
        license_rec = self.env['license'].create({
            'name': 'Test License Expiring',
            'customer_id': self.partner.id,
            'license_types_id': self.license_type.id,
            'issued_company_id': self.company.id,
            'project_id': self.project.id,
            'task_id': self.task.id,
            'product_id': self.product.id,
            'description': 'Test License Description',
            'start_date': Date.subtract(Date.today(), days=10),
            'expire_date': Date.today(),
            'expire_remainder_day': 2,
        })
        
        self.env['license'].license_expiry_action()
        self.assertTrue(license_rec.has_expired)
        self.assertEqual(license_rec.state, 'expired')

    def test_05_license_report(self):
        """Test PDF report action"""
        license_rec = self.env['license'].create({
            'name': 'Test License Report',
            'customer_id': self.partner.id,
            'license_types_id': self.license_type.id,
            'issued_company_id': self.company.id,
            'project_id': self.project.id,
            'task_id': self.task.id,
            'product_id': self.product.id,
            'description': 'Test License Description',
            'start_date': Date.today(),
            'expire_date': Date.add(Date.today(), days=10),
        })
        action = license_rec.action_create_license_pdf_report()
        self.assertEqual(action['type'], 'ir.actions.report')

    def test_06_partner_license_count(self):
        """Test res.partner license count and smart button"""
        self.env['license'].create({
            'name': 'Test License 1',
            'customer_id': self.partner.id,
            'license_types_id': self.license_type.id,
            'issued_company_id': self.company.id,
            'project_id': self.project.id,
            'task_id': self.task.id,
            'product_id': self.product.id,
            'description': 'Test License Description',
            'start_date': Date.today(),
            'expire_date': Date.add(Date.today(), days=10),
        })
        self.partner._compute_total_license_count()
        self.assertEqual(self.partner.license_count, 1)
        
        action = self.partner.show_license()
        self.assertEqual(action['res_model'], 'license')
        self.assertEqual(action['domain'], [('customer_id', '=', self.partner.id)])
