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
##############################################################################
from odoo.tests.common import TransactionCase
from odoo import fields

class TestAnimalTraining(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestAnimalTraining, cls).setUpClass()

        cls.owner = cls.env['res.partner'].create({
            'name': 'Training Test Owner',
            'phone': '9876543211',
            'email': 'trainingowner@test.com'
        })

        cls.animal_type = cls.env['animal.types'].create({
            'name': 'Dog'
        })

        cls.patient = cls.env['res.patient'].create({
            'name': 'Rex',
            'pet_type_id': cls.animal_type.id,
            'gender': 'male',
            'age': 1,
            'owner_name_id': cls.owner.id,
        })

        cls.training_product = cls.env['product.product'].create({
            'name': 'Training',
            'type': 'service',
            'list_price': 0.0,
        })

        cls.training_package = cls.env['training.package'].create({
            'name': 'Basic Obedience',
            'days': 10,
            'charge': 150.0,
        })

        cls.trainer = cls.env['res.partner'].create({
            'name': 'Trainer Bob',
        })

    def test_01_training_creation(self):
        """Test animal training creation and auto sequence."""
        training = self.env['animal.training'].create({
            'animal_id': self.patient.id,
            'training_emp_id': self.trainer.id,
            'appointment_date': fields.Date.today(),
            'package_id': self.training_package.id,
        })

        self.assertTrue(training.training_no, "Training No should be generated")
        self.assertEqual(training.state, 'draft', "Default state should be draft")
        self.assertEqual(training.animal_id, self.patient, "Patient should match")
        self.assertEqual(training.charge, 150.0, "Charge should be fetched from package")

    def test_02_create_invoice(self):
        """Test successful invoice creation."""
        training = self.env['animal.training'].create({
            'animal_id': self.patient.id,
            'training_emp_id': self.trainer.id,
            'package_id': self.training_package.id,
        })
        
        # Create Invoice
        action = training.action_create_invoice()
        
        self.assertTrue(training.is_invoice, "is_invoice should be True")
        self.assertTrue(training.training_invoice_id, "Invoice should be created and linked")
        
        invoice = training.training_invoice_id
        self.assertEqual(invoice.move_type, 'out_invoice', "Invoice type should be out_invoice")
        self.assertEqual(invoice.partner_id, self.owner, "Invoice should be billed to owner")
        self.assertEqual(len(invoice.invoice_line_ids), 1, "Invoice should have 1 line")
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, 150.0, "Invoice line price should be 150.0")
