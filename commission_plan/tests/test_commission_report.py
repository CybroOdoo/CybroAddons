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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import io
import json
from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestCommissionReport(TransactionCase):
    """Test suite for the commission report wizard and its XLSX export."""

    def setUp(self):
        super().setUp()
        self.ReportWizard = self.env['commission.report']
        self.commission = self.env['crm.commission'].create({
            'name': 'Report Plan',
            'date_from': date.today(),
            'date_to': date.today(),
            'type': 'product',
        })
        self.user = self.env['res.users'].create({
            'name': 'Report User',
            'login': 'report_user',
            'commission_id': self.commission.id,
        })
        self.team = self.env['crm.team'].create({
            'name': 'Report Team',
            'commission_id': self.commission.id,
        })
        self.env['crm.team.member'].create({
            'crm_team_id': self.team.id,
            'user_id': self.user.id,
        })
        # Create a minimal sale order and a persisted commission line so that
        # _fetch_stored_commissions returns data when the report is generated.
        partner = self.env['res.partner'].create({'name': 'Report Partner'})
        self.sale_order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'user_id': self.user.id,
            'team_id': self.team.id,
        })
        self.env['sale.order.commission'].create({
            'order_id': self.sale_order.id,
            'user_id': self.user.id,
            'team_id': self.team.id,
            'commission_id': self.commission.id,
            'plan_source': 'team',
            'revenue': 1000.0,
            'rate': 10.0,
            'amount': 100.0,
            'commission_type': 'earned',
        })

    def test_onchange_salesperson_ids(self):
        """Test onchange computes is_sales_person correctly"""
        wizard = self.ReportWizard.create({})
        wizard.salesperson_ids = [(4, self.user.id)]
        wizard._onchange_salesperson_ids()
        self.assertTrue(wizard.is_sales_person)

    def test_onchange_sales_team_ids(self):
        """Test onchange computes is_sales_team correctly"""
        wizard = self.ReportWizard.create({})
        wizard.sales_team_ids = [(4, self.team.id)]
        wizard._onchange_sales_team_ids()
        self.assertTrue(wizard.is_sales_team)

    def test_sales_team_constrains(self):
        """Test report constraints"""
        # Empty team without members should raise error
        empty_team = self.env['crm.team'].create({'name': 'Empty Team'})
        with self.assertRaises(ValidationError):
            self.ReportWizard.create({
                'sales_team_ids': [(4, empty_team.id)]
            })

        # Salesperson without commission plan should raise error
        user_no_comm = self.env['res.users'].create({
            'name': 'No Comm User', 'login': 'no_comm'
        })
        with self.assertRaises(ValidationError):
            self.ReportWizard.create({
                'salesperson_ids': [(4, user_no_comm.id)]
            })

    def test_action_print_xlsx_report(self):
        """Test action printing xlsx report logic"""
        wizard = self.ReportWizard.create({
            'sales_team_ids': [(4, self.team.id)]
        })
        res = wizard.action_print_xlsx_report()
        self.assertEqual(res.get('type'), 'ir.actions.report')
        self.assertEqual(res.get('report_type'), 'xlsx')

    def test_action_print_xlsx_report_salesperson(self):
        """Test action printing xlsx report for salespeople"""
        wizard = self.ReportWizard.create({
            'salesperson_ids': [(4, self.user.id)]
        })
        res = wizard.action_print_xlsx_report()
        self.assertEqual(res.get('type'), 'ir.actions.report')
        self.assertEqual(res.get('report_type'), 'xlsx')

    def test_get_xlsx_report(self):
        """Test get_xlsx_report renders binary output for team and user"""
        class MockResponse:
            """Minimal response mock with a stream for get_xlsx_report."""
            def __init__(self):
                self.stream = io.BytesIO()

        # Test sales team section
        wizard_team = self.ReportWizard.create({
            'sales_team_ids': [(4, self.team.id)]
        })
        res_team = wizard_team.action_print_xlsx_report()
        options_team = json.loads(res_team['data']['options'])
        resp_team = MockResponse()
        wizard_team.get_xlsx_report(options_team, resp_team)
        self.assertGreater(len(resp_team.stream.getvalue()), 0)

        # Test salesperson section
        wizard_user = self.ReportWizard.create({
            'salesperson_ids': [(4, self.user.id)]
        })
        res_user = wizard_user.action_print_xlsx_report()
        options_user = json.loads(res_user['data']['options'])
        resp_user = MockResponse()
        wizard_user.get_xlsx_report(options_user, resp_user)
        self.assertGreater(len(resp_user.stream.getvalue()), 0)
