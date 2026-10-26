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

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import PharmaRetentionCommon


@tagged('post_install', '-at_install')
class TestRetentionDisposal(PharmaRetentionCommon):
    """Approved disposal of reserve samples."""

    def dispose(self, sample, user=None):
        """Run the disposal wizard on ``sample`` as ``user`` (QA by default)."""
        wizard = self.env['pharma.retention.disposal.wizard'].with_user(
            user or self.qa_user).create({
                'sample_id': sample.id,
                'disposal_method': 'incineration',
                'disposal_reference': 'WN-001',
                'disposal_note': 'Witnessed',
            })
        return wizard.action_confirm()

    def test_dispose_due_sample(self):
        """QA disposes of a sample whose retention period has expired."""
        sample = self.retained_sample()
        self.assertTrue(sample.is_disposal_due)
        self.dispose(sample)
        self.assertEqual(sample.state, 'disposed')
        self.assertEqual(sample.disposed_by, self.qa_user)
        self.assertEqual(sample.disposal_method, 'incineration')
        self.assertFalse(sample.is_disposal_due)
        with self.assertRaises(UserError):
            self.dispose(sample)
        with self.assertRaises(UserError):
            sample.container = 'Changed'
        with self.assertRaises(UserError):
            self.withdraw(sample, 1.0)

    def test_dispose_not_due(self):
        """Disposal waits for the retention period to expire."""
        sample = self.retained_sample(lot=self.released_lot(expiry=date(2999, 1, 1)))
        self.assertFalse(sample.is_disposal_due)
        with self.assertRaises(UserError):
            self.dispose(sample)

    def test_dispose_no_expiry(self):
        """Without a batch expiry the disposal date is unknown."""
        sample = self.retained_sample(lot=self.released_lot(expiry=False))
        self.assertFalse(sample.disposal_due_date)
        with self.assertRaises(UserError):
            self.dispose(sample)

    def test_dispose_requires_qa(self):
        """Only quality management can approve a disposal."""
        sample = self.retained_sample()
        wizard = self.env['pharma.retention.disposal.wizard'].create({
            'sample_id': sample.id, 'disposal_method': 'other', 'disposal_note': 'x',
        })
        with self.assertRaises(UserError):
            wizard.with_user(self.operator).action_confirm()
