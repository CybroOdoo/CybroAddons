# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from datetime import date
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'pet_shop_management')
class TestReportPetInformation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Report Pet Owner',
        })
        cls.pet = cls.env['product.product'].create({
            'name': 'Bella',
            'is_pet': True,
            'dob': date(2023, 1, 1),
            'sex': 'female',
            'customer_id': cls.partner.id,
            'is_allergy': True,
            'is_reaction': False,
            'pet_food': 'Pedigree',
        })

    def test_01_report_values(self):
        """ Test _get_report_values returns correct document context """
        report_model = self.env[
            'report.pet_shop_management.report_pet_information'
        ]
        vals = report_model._get_report_values(
            [self.pet.id], data={'custom_data': 123}
        )

        self.assertEqual(vals.get('doc_ids'), [self.pet.id])
        self.assertEqual(vals.get('doc_model'), 'product.product')
        self.assertEqual(vals.get('docs'), self.pet)
        self.assertEqual(vals.get('data'), {'custom_data': 123})

    def test_02_pdf_report_rendering(self):
        """ Test QWeb report renders successfully without syntax errors """
        report_action = self.env.ref('pet_shop_management.action_pet_report')
        html_content, _ = report_action._render_qweb_html(
            report_action.id, [self.pet.id]
        )
        self.assertTrue(html_content)
        self.assertIn(b'Bella', html_content)

    def test_03_multi_pet_report_rendering(self):
        """ Test printing report for multiple selected pets simultaneously """
        pet2 = self.env['product.product'].create({
            'name': 'Max',
            'is_pet': True,
            'dob': date(2022, 5, 10),
            'sex': 'male',
            'customer_id': self.partner.id,
        })
        report_action = self.env.ref('pet_shop_management.action_pet_report')
        html_content, _ = report_action._render_qweb_html(
            report_action.id, [self.pet.id, pet2.id]
        )
        self.assertTrue(html_content)
        self.assertIn(b'Bella', html_content)
        self.assertIn(b'Max', html_content)
