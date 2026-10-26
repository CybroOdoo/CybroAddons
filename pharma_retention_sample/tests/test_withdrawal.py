# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import PharmaRetentionCommon


@tagged('post_install', '-at_install')
class TestRetentionWithdrawal(PharmaRetentionCommon):
    """Withdrawals and periodic examinations."""

    def test_withdrawal_updates_quantities(self):
        """Withdrawn and remaining quantities follow the withdrawals."""
        sample = self.retained_sample()
        self.withdraw(sample, 3.0, reference='CMP-1')
        self.withdraw(sample, 2.0, purpose='complaint')
        self.assertEqual(sample.withdrawn_qty, 5.0)
        self.assertEqual(sample.remaining_qty, 5.0)
        self.assertEqual(len(sample.withdrawal_ids), 2)

    def test_withdrawal_limits(self):
        """No more than the remaining quantity, in one create or several."""
        sample = self.retained_sample()
        with self.assertRaises(UserError):
            self.withdraw(sample, 11.0)
        Withdrawal = self.env['pharma.retention.withdrawal'].with_user(self.operator)
        vals = {'sample_id': sample.id, 'purpose': 'retest', 'quantity': 6.0, 'reason': 'x'}
        with self.assertRaises(UserError):
            Withdrawal.create([vals, vals])

    def test_withdrawal_needs_retained_sample(self):
        """A draft sample cannot supply a withdrawal."""
        sample = self.draft_sample()
        with self.assertRaises(UserError):
            self.withdraw(sample, 1.0)

    def test_withdrawal_validation(self):
        """Quantity and examination result rules."""
        sample = self.retained_sample()
        with self.assertRaises(ValidationError):
            self.withdraw(sample, 0.0)
        with self.assertRaises(ValidationError):
            self.withdraw(sample, 0.0, purpose='periodic_exam')
        with self.assertRaises(ValidationError):
            self.withdraw(sample, -1.0)

    def test_periodic_exam(self):
        """An examination rolls the schedule forward; a bad result is posted."""
        sample = self.retained_sample()
        self.withdraw(sample, 0.0, purpose='periodic_exam',
                      exam_result='unsatisfactory', date=date(2024, 3, 1))
        self.assertEqual(sample.last_exam_date, date(2024, 3, 1))
        self.assertEqual(sample.next_exam_date, date(2024, 9, 1))
        self.assertTrue(any('UNSATISFACTORY' in m.body for m in sample.message_ids))

    def test_withdrawal_is_immutable(self):
        """Recorded withdrawals cannot be changed or deleted."""
        withdrawal = self.withdraw(self.retained_sample(), 1.0).sudo()
        with self.assertRaises(UserError):
            withdrawal.reason = 'Changed'
        with self.assertRaises(UserError):
            withdrawal.unlink()
