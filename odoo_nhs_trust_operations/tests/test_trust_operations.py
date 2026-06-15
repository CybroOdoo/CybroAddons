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

from odoo.tests import tagged

from .common import NhsOpsCommon


@tagged('post_install', '-at_install')
class TestTrustOperations(NhsOpsCommon):
    """Operational computed fields injected onto nhs.trust."""

    def test_site_and_department_counts(self):
        """site_count counts sites; department_count sums departments across sites."""
        self.assertEqual(self.trust_en.site_count, 1)
        self.assertEqual(self.trust_en.department_count, 1)
        # add a second site with a department
        site2 = self.Site.create({
            'name': 'Whipps Cross', 'trust_id': self.trust_en.id,
            'site_type': 'community_hospital', 'bed_capacity': 50,
        })
        self.Dept.create({'name': 'Pharmacy', 'site_id': site2.id,
                          'department_type': 'support'})
        self.assertEqual(self.trust_en.site_count, 2)
        self.assertEqual(self.trust_en.department_count, 2)

    def test_total_bed_capacity_sum_and_override(self):
        """total_bed_capacity sums site beds, unless manual override is set."""
        self.assertEqual(self.trust_en.total_bed_capacity, 100)  # one site, 100 beds
        self.Site.create({'name': 'Annex', 'trust_id': self.trust_en.id,
                          'site_type': 'clinic', 'bed_capacity': 25})
        self.assertEqual(self.trust_en.total_bed_capacity, 125)
        # manual override wins
        self.trust_en.manual_bed_capacity = 999
        self.assertEqual(self.trust_en.total_bed_capacity, 999)

    def test_surplus_deficit(self):
        """surplus_deficit = annual_income - annual_expenditure."""
        self.trust_en.write({'annual_income': 1_000_000, 'annual_expenditure': 750_000})
        self.assertEqual(self.trust_en.surplus_deficit, 250_000)
        self.trust_en.annual_expenditure = 1_200_000
        self.assertEqual(self.trust_en.surplus_deficit, -200_000)

    def test_latest_cqc_picks_most_recent_active(self):
        """latest_cqc_* reflect the most recent inspection; rating/date come from
        the most recent ACTIVE inspection."""
        self.Cqc.create({
            'trust_id': self.trust_en.id, 'inspection_date': date(2024, 1, 1),
            'overall_rating': 'good', 'state': 'draft',
            'cqc_registration_status': 'registered',
        })
        self.Cqc.create({
            'trust_id': self.trust_en.id, 'inspection_date': date(2025, 1, 1),
            'overall_rating': 'outstanding', 'state': 'active',
            'cqc_registration_status': 'conditions',
        })
        t = self.trust_en
        self.assertEqual(t.latest_cqc_status, 'active')          # newest inspection's state
        self.assertEqual(t.cqc_registration_status, 'conditions')  # newest inspection's reg
        self.assertEqual(t.latest_cqc_rating, 'outstanding')     # newest ACTIVE rating
        self.assertEqual(t.latest_cqc_date, date(2025, 1, 1))

    def test_england_no_inspection_is_pending(self):
        """An England trust with no inspections is 'pending', no rating."""
        self.assertEqual(self.trust_en.cqc_registration_status, 'pending')
        self.assertFalse(self.trust_en.latest_cqc_rating)

    def test_scotland_cqc_not_applicable(self):
        """Scotland trusts are 'not_applicable' with no CQC rating."""
        self.assertEqual(self.trust_sco.cqc_registration_status, 'not_applicable')
        self.assertFalse(self.trust_sco.latest_cqc_rating)
