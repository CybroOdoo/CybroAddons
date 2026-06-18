# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import date, timedelta

class TestProfitLossReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestProfitLossReport, cls).setUpClass()
        cls.company = cls.env.user.company_id
        
    def test_01_invalid_dates(self):
        """Test that start date cannot be after end date."""
        with self.assertRaises(ValidationError):
            self.env['profit.loss.report'].create({
                'start_date': date.today() + timedelta(days=1),
                'end_date': date.today(),
            })

    def test_02_action_print_report(self):
        """Test that the report action returns correctly."""
        wizard = self.env['profit.loss.report'].create({
            'start_date': date.today().replace(day=1),
            'end_date': date.today() + timedelta(days=30),
        })
        
        res = wizard.action_button_to_print_pdf()
        
        self.assertIsInstance(res, dict)
        self.assertIn(res.get('type'), ['ir.actions.report', 'ir.actions.act_window'])
