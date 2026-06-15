# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aleena K (odoo@cybrosys.com)
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
from unittest.mock import MagicMock
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo.fields import Date
from odoo.http import _request_stack

class TestSalesPerformance(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Use standard active company
        cls.company = cls.env.company
        
        # Create warehouse
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'Test Warehouse',
            'code': 'TWH',
            'company_id': cls.company.id,
        })

        # Create sales team
        cls.sales_team = cls.env['crm.team'].create({
            'name': 'Test Sales Team',
            'company_id': cls.company.id,
        })
        
        # Create users
        cls.sales_person_1 = cls.env['res.users'].create({
            'name': 'Test Sales Person 1',
            'login': 'test_sales_person_1',
            'email': 'test1@example.com',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
        })
        cls.sales_person_2 = cls.env['res.users'].create({
            'name': 'Test Sales Person 2',
            'login': 'test_sales_person_2',
            'email': 'test2@example.com',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
        })

        # Create crm.team.member records to compute sale_team_id
        cls.env['crm.team.member'].create({
            'crm_team_id': cls.sales_team.id,
            'user_id': cls.sales_person_1.id,
        })
        cls.env['crm.team.member'].create({
            'crm_team_id': cls.sales_team.id,
            'user_id': cls.sales_person_2.id,
        })

        # Create partner and a dummy sale order to avoid ZeroDivisionError
        partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': partner.id,
            'user_id': cls.sales_person_1.id,
            'team_id': cls.sales_team.id,
            'company_id': cls.company.id,
        })

    def setUp(self):
        super().setUp()
        self.mock_request = MagicMock()
        self.mock_request.env = self.env
        _request_stack.push(self.mock_request)

    def tearDown(self):
        _request_stack.pop()
        super().tearDown()

    def test_date_validation(self):
        # End date before start date should raise UserError
        with self.assertRaises(UserError):
            self.env['sales.performance'].create({
                'start_date': '2026-06-15',
                'end_date': '2026-06-10',
            })

    def test_sales_performance_with_persons(self):
        wizard = self.env['sales.performance'].create({
            'sales_person_ids': [(6, 0, [self.sales_person_1.id])],
            'company_ids': [(6, 0, [self.company.id])],
            'up_to_date_report': True,
        })
        
        action = wizard.sales_performance()
        self.assertEqual(action.get('res_model'), 'res.users')
        self.assertIn(self.sales_person_1.id, action.get('domain')[0][2])

    def test_sales_performance_with_teams(self):
        wizard = self.env['sales.performance'].create({
            'sales_team_ids': [(6, 0, [self.sales_team.id])],
            'company_ids': [(6, 0, [self.company.id])],
            'up_to_date_report': True,
        })
        
        action = wizard.sales_performance()
        self.assertEqual(action.get('res_model'), 'res.users')
        self.assertIn(self.sales_person_1.id, action.get('domain')[0][2])
        self.assertIn(self.sales_person_2.id, action.get('domain')[0][2])

    def test_sales_performance_with_companies_only(self):
        wizard = self.env['sales.performance'].create({
            'company_ids': [(6, 0, [self.company.id])],
            'up_to_date_report': True,
        })
        
        action = wizard.sales_performance()
        self.assertEqual(action.get('res_model'), 'res.users')
        self.assertIn(self.sales_person_1.id, action.get('domain')[0][2])
        self.assertIn(self.sales_person_2.id, action.get('domain')[0][2])

    def test_sales_performance_no_sales_team_error(self):
        # Create empty company
        empty_company = self.env['res.company'].create({
            'name': 'Empty Company',
        })
        # Note: If no sales person exists for the empty company, it should raise UserError
        wizard = self.env['sales.performance'].create({
            'company_ids': [(6, 0, [empty_company.id])],
        })
        
        with self.assertRaises(UserError):
            wizard.sales_performance()

