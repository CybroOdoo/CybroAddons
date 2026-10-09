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
from datetime import date

from freezegun import freeze_time

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import AiAccountingCommon


@tagged('post_install', '-at_install')
@freeze_time('2026-10-15')
class TestPeriod(AiAccountingCommon):

    def resolve(self, period, **kwargs):
        return self.toolkit._ai_resolve_period(dict(period=period, **kwargs))

    def test_calendar_periods(self):
        self.assertEqual(self.resolve('today'), (date(2026, 10, 15), date(2026, 10, 15)))
        self.assertEqual(self.resolve('this_month'), (date(2026, 10, 1), date(2026, 10, 31)))
        self.assertEqual(self.resolve('last_month'), (date(2026, 9, 1), date(2026, 9, 30)))
        self.assertEqual(self.resolve('this_quarter'), (date(2026, 10, 1), date(2026, 12, 31)))
        self.assertEqual(self.resolve('last_quarter'), (date(2026, 7, 1), date(2026, 9, 30)))
        self.assertEqual(self.resolve('this_week'), (date(2026, 10, 12), date(2026, 10, 18)))
        self.assertEqual(self.resolve('last_30_days'), (date(2026, 9, 16), date(2026, 10, 15)))
        self.assertEqual(self.resolve('last_12_months'), (date(2025, 11, 1), date(2026, 10, 31)))
        self.assertEqual(self.resolve('all_time'), (False, date(2026, 10, 15)))

    def test_fiscal_year_periods(self):
        self.env.company.write({'fiscalyear_last_month': '3', 'fiscalyear_last_day': 31})
        self.assertEqual(self.resolve('this_year'), (date(2026, 4, 1), date(2027, 3, 31)))
        self.assertEqual(self.resolve('last_year'), (date(2025, 4, 1), date(2026, 3, 31)))
        self.assertEqual(self.resolve('year_to_date'), (date(2026, 4, 1), date(2026, 10, 15)))

    def test_custom_period(self):
        self.assertEqual(self.resolve('custom', date_from='2026-01-01', date_to='2026-01-31'),
                         (date(2026, 1, 1), date(2026, 1, 31)))
        with self.assertRaises(UserError):
            self.resolve('custom', date_from='2026-02-01', date_to='2026-01-31')
        with self.assertRaises(UserError):
            self.resolve('custom', date_from='not a date')

    def test_previous_period(self):
        previous = self.toolkit._ai_previous_period
        self.assertEqual(previous(date(2026, 10, 1), date(2026, 10, 31), 'previous_period'),
                         (date(2026, 9, 1), date(2026, 9, 30)))
        self.assertEqual(previous(date(2026, 7, 1), date(2026, 9, 30), 'previous_period'),
                         (date(2026, 4, 1), date(2026, 6, 30)))
        self.assertEqual(previous(date(2026, 10, 1), date(2026, 10, 31), 'previous_year'),
                         (date(2025, 10, 1), date(2025, 10, 31)))
        self.assertEqual(previous(date(2026, 10, 6), date(2026, 10, 15), 'previous_period'),
                         (date(2026, 9, 26), date(2026, 10, 5)))
