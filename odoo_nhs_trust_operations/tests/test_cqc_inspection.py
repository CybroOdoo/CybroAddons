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

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import NhsOpsCommon


@tagged('post_install', '-at_install')
class TestCqcInspection(NhsOpsCommon):
    """CQC inspection constraints, workflow and display name."""

    def _make(self, **kw):
        vals = {
            'trust_id': self.trust_en.id,
            'inspection_date': date(2025, 1, 1),
            'overall_rating': 'good',
        }
        vals.update(kw)
        return self.Cqc.create(vals)

    def test_cqc_only_for_england(self):
        """A CQC inspection cannot be attached to a Scotland trust."""
        with self.assertRaises(ValidationError):
            self._make(trust_id=self.trust_sco.id)

    def test_next_inspection_after_inspection_date(self):
        """next_inspection_due must be after inspection_date."""
        with self.assertRaises(ValidationError):
            self._make(inspection_date=date(2025, 6, 1),
                       next_inspection_due=date(2025, 1, 1))

    def test_state_workflow_buttons(self):
        """submit -> under_review, approve -> active, reset -> draft."""
        insp = self._make()
        self.assertEqual(insp.state, 'draft')
        insp.action_submit()
        self.assertEqual(insp.state, 'under_review')
        insp.action_approve()
        self.assertEqual(insp.state, 'active')
        insp.action_reset_to_draft()
        self.assertEqual(insp.state, 'draft')

    def test_display_name(self):
        """display_name combines trust, date and rating label."""
        insp = self._make(overall_rating='outstanding')
        self.assertIn('Outstanding', insp.display_name)
        self.assertIn('2025-01-01', insp.display_name)
