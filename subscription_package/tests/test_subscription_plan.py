# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase

class TestSubscriptionPlan(TransactionCase):
    """Test Subscription Package Plan Model"""

    def setUp(self):
        """Setup test variables"""
        super(TestSubscriptionPlan, self).setUp()
        self.Plan = self.env['subscription.package.plan']

    def test_compute_renewal_time_days(self):
        """Test renewal time computation for days"""
        plan = self.Plan.create({
            'name': '10 Days Plan',
            'renewal_value': '10',
            'renewal_period': 'days'
        })
        self.assertEqual(plan.renewal_time, 10)

    def test_compute_renewal_time_months(self):
        """Test renewal time computation for months"""
        plan = self.Plan.create({
            'name': '2 Months Plan',
            'renewal_value': '2',
            'renewal_period': 'months'
        })
        # Logic: int(rec.renewal_value) * 28
        self.assertEqual(plan.renewal_time, 56)

    def test_compute_days_to_end_custom(self):
        """Test days to end for custom limit"""
        plan = self.Plan.create({
            'name': 'Custom Plan',
            'renewal_value': '1',
            'renewal_period': 'months',
            'limit_choice': 'custom',
            'limit_count': 3
        })
        # Logic: 28 * 3 = 84
        self.assertEqual(plan.days_to_end, 84)

    def test_display_name(self):
        """Test plan display name"""
        plan = self.Plan.create({
            'name': 'Standard Plan',
            'short_code': 'STA',
            'renewal_value': '1',
            'renewal_period': 'months'
        })
        self.assertEqual(plan.display_name, 'STA - Standard Plan')

    def test_compute_renewal_time_weeks_and_years(self):
        """Test renewal time computation for weeks and years"""
        plan_weeks = self.Plan.create({
            'name': '2 Weeks Plan',
            'renewal_value': '2',
            'renewal_period': 'weeks'
        })
        self.assertEqual(plan_weeks.renewal_time, 14)

        plan_years = self.Plan.create({
            'name': '1 Year Plan',
            'renewal_value': '1',
            'renewal_period': 'years'
        })
        self.assertEqual(plan_years.renewal_time, 364)

    def test_compute_renewal_time_invalid_and_negative(self):
        """Test renewal time computation with non-integer or <= 0 value"""
        plan_inv = self.Plan.create({
            'name': 'Invalid Val Plan',
            'renewal_value': 'invalid_str',
            'renewal_period': 'days'
        })
        self.assertEqual(plan_inv.renewal_time, 1)

        plan_neg = self.Plan.create({
            'name': 'Negative Val Plan',
            'renewal_value': '-5',
            'renewal_period': 'days'
        })
        self.assertEqual(plan_neg.renewal_time, 1)

    def test_compute_days_to_end_manual_and_ones(self):
        """Test days to end for manual and ones limit choice"""
        plan_manual = self.Plan.create({
            'name': 'Manual Plan',
            'renewal_value': '1',
            'renewal_period': 'months',
            'limit_choice': 'manual',
        })
        self.assertEqual(plan_manual.days_to_end, 0)

        plan_ones = self.Plan.create({
            'name': 'Ones Plan',
            'renewal_value': '1',
            'renewal_period': 'months',
            'limit_choice': 'ones',
        })
        self.assertEqual(plan_ones.days_to_end, 28)

        # Fallback else branches
        plan_other = self.Plan.create({
            'name': 'Other Fallback Plan',
            'renewal_period': False,
            'limit_choice': False,
        })
        plan_other._compute_renewal_time()
        self.assertEqual(plan_other.renewal_time, 1)
        plan_other._compute_days_to_end()
        self.assertEqual(plan_other.days_to_end, 1)

    def test_plan_buttons_and_counts(self):
        """Test plan smart buttons and counts"""
        plan = self.Plan.create({
            'name': 'Count Test Plan',
            'renewal_value': '1',
            'renewal_period': 'months',
        })
        self.env['product.product'].create({
            'name': 'Plan Test Product',
            'is_subscription': True,
            'subscription_plan_id': plan.id,
        })
        self.assertGreaterEqual(plan.product_count, 1)
        action_prod = plan.button_product_count()
        self.assertEqual(action_prod['res_model'], 'product.product')

        partner = self.env['res.partner'].create({'name': 'Plan Test Partner'})
        self.env['subscription.package'].create({
            'name': 'Plan Test Sub',
            'partner_id': partner.id,
            'plan_id': plan.id,
        })
        self.assertGreaterEqual(plan.subscription_count, 1)
        action_sub = plan.button_sub_count()
        self.assertEqual(action_sub['name'], 'Subscriptions')

    def test_display_name_without_short_code(self):
        """Test display name when short code is empty"""
        plan = self.Plan.create({
            'name': 'No Code Plan',
            'renewal_value': '1',
            'renewal_period': 'months',
        })
        plan.short_code = False
        plan._compute_display_name()
        self.assertEqual(plan.display_name, 'No Code Plan')
