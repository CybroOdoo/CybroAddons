# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from datetime import date, timedelta


class TestTimesheetReport(TransactionCase):

    def setUp(self):
        super(TestTimesheetReport, self).setUp()
        
        self.company = self.env['res.company'].create({'name': 'Test Company'})
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user_timesheet',
            'company_id': self.company.id,
            'company_ids': [(6, 0, [self.company.id])],
        })
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
            'user_id': self.user.id,
            'company_id': self.company.id,
        })
        
        self.project = self.env['project.project'].create({
            'name': 'Test Project',
        })
        
        today = date.today()
        self.timesheet1 = self.env['account.analytic.line'].create({
            'name': 'Test Timesheet 1',
            'project_id': self.project.id,
            'user_id': self.user.id,
            'date': today - timedelta(days=2),
            'unit_amount': 2.0,
        })
        
        self.timesheet2 = self.env['account.analytic.line'].create({
            'name': 'Test Timesheet 2',
            'project_id': self.project.id,
            'user_id': self.user.id,
            'date': today - timedelta(days=5),
            'unit_amount': 3.0,
        })

    def test_timesheet_report_wizard_dates(self):
        """Test the validation of dates in the timesheet report wizard."""
        today = date.today()
        
        # Test start date > end date
        wizard_invalid_dates = self.env['timesheet.report'].create({
            'user_id': self.user.id,
            'from_date': today,
            'to_date': today - timedelta(days=1),
        })
        with self.assertRaises(UserError):
            wizard_invalid_dates.print_timesheet()
            
        # Test future dates
        wizard_future_dates = self.env['timesheet.report'].create({
            'user_id': self.user.id,
            'from_date': today + timedelta(days=1),
            'to_date': today + timedelta(days=2),
        })
        with self.assertRaises(UserError):
            wizard_future_dates.print_timesheet()
            
        # Test valid dates
        wizard_valid = self.env['timesheet.report'].with_context(discard_logo_check=True).create({
            'user_id': self.user.id,
            'from_date': today - timedelta(days=5),
            'to_date': today,
        })
        action = wizard_valid.print_timesheet()
        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['data']['employee'], self.user.id)
        self.assertEqual(action['data']['start_date'], today - timedelta(days=5))
        self.assertEqual(action['data']['end_date'], today)

    def test_report_get_timesheets(self):
        """Test get_timesheets and _get_report_values methods of the report."""
        today = date.today()
        report_model = self.env['report.timesheets_by_employee.report_timesheet_employee']
        
        # Test with both from_date and to_date
        wizard = self.env['timesheet.report'].create({
            'user_id': self.user.id,
            'from_date': today - timedelta(days=3),
            'to_date': today,
        })
        
        # Only timesheet1 should be included
        records, total = report_model.get_timesheets(wizard)
        self.assertEqual(total, 2.0)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['project'], self.project.name)
        
        # Test with only from_date
        wizard_from = self.env['timesheet.report'].create({
            'user_id': self.user.id,
            'from_date': today - timedelta(days=6),
        })
        records, total = report_model.get_timesheets(wizard_from)
        self.assertEqual(total, 5.0) # Both timesheets
        self.assertEqual(len(records), 2)
        
        # Test with only to_date
        wizard_to = self.env['timesheet.report'].create({
            'user_id': self.user.id,
            'to_date': today - timedelta(days=4),
        })
        records, total = report_model.get_timesheets(wizard_to)
        self.assertEqual(total, 3.0) # Only timesheet2
        self.assertEqual(len(records), 1)
        
        # Test without dates
        wizard_no_dates = self.env['timesheet.report'].create({
            'user_id': self.user.id,
        })
        records, total = report_model.get_timesheets(wizard_no_dates)
        self.assertEqual(total, 5.0)
        self.assertEqual(len(records), 2)
        
        # Test _get_report_values
        wizard.with_context(active_id=wizard.id)
        report_values = report_model.with_context(active_id=wizard.id)._get_report_values(wizard.ids, data={})
        self.assertIn('timesheets', report_values)
        self.assertIn('total', report_values)
        self.assertIn('company', report_values)
        self.assertEqual(report_values['total'], 2.0)
        self.assertEqual(report_values['company'].id, self.company.id)
        self.assertEqual(report_values['period'], f"From {today - timedelta(days=3)} To {today}")

    def test_report_get_report_values_multiple_identification(self):
        """Test _get_report_values method when multiple employee ids exist."""
        # Create a second company to avoid unique constraint (user_id, company_id)
        company2 = self.env['res.company'].create({'name': 'Test Company 2'})
        self.user.write({'company_ids': [(4, company2.id)]})

        # Create a second employee linked to the same user but different company
        self.env['hr.employee'].create({
            'name': 'Test Employee 2',
            'user_id': self.user.id,
            'company_id': company2.id,
        })
        
        today = date.today()
        wizard = self.env['timesheet.report'].create({
            'user_id': self.user.id,
            'from_date': today - timedelta(days=3),
            'to_date': today,
        })
        
        report_model = self.env['report.timesheets_by_employee.report_timesheet_employee']
        report_values = report_model.with_context(active_id=wizard.id)._get_report_values(wizard.ids, data={'test': 'data'})
        
        self.assertEqual(len(report_values['identification']), 2)
        self.assertIn('data', report_values)
