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
#############################################################################
import calendar
from datetime import date, timedelta
from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.addons.crm_dashboard.models.crm_lead import get_period_start_date


@tagged('post_install', '-at_install')
class TestCrmLeadDashboard(TransactionCase):
    """Test cases for the dashboard data methods on crm.lead"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Lead = cls.env['crm.lead']
        cls.salesman_group = cls.env.ref('sales_team.group_sale_salesman')
        cls.sales_user = cls.env['res.users'].create({
            'name': 'Dashboard Salesperson',
            'login': 'crm_dashboard_salesperson',
            'email': 'crm_dashboard_salesperson@example.com',
            'group_ids': [(6, 0, [cls.salesman_group.id])],
        })
        cls.other_user = cls.env['res.users'].create({
            'name': 'Dashboard Other Salesperson',
            'login': 'crm_dashboard_other_salesperson',
            'email': 'crm_dashboard_other@example.com',
            'group_ids': [(6, 0, [cls.salesman_group.id])],
        })
        cls.admin_user = cls.env.ref('base.user_admin')
        cls.lead_model = cls.env.ref('crm.model_crm_lead')
        cls.activity_type = cls.env['mail.activity.type'].create({
            'name': 'Dashboard Test Activity',
            'res_model': 'crm.lead',
        })
        cls.today = fields.Date.today()

    def _create_activity(self, lead, user, deadline, summary):
        """Create a mail activity on the given lead"""
        return self.env['mail.activity'].create({
            'res_model_id': self.lead_model.id,
            'res_id': lead.id,
            'activity_type_id': self.activity_type.id,
            'user_id': user.id,
            'date_deadline': deadline,
            'summary': summary,
        })

    # ------------------------------------------------------------------
    # get_period_start_date
    # ------------------------------------------------------------------
    def test_period_start_date_month(self):
        """Month period starts on the first day of the current month"""
        start = get_period_start_date('month')
        today = date.today()
        self.assertEqual(start, today.replace(day=1))

    def test_period_start_date_quarter(self):
        """Quarter period starts on the first day of the current quarter"""
        start = get_period_start_date('quarter')
        today = date.today()
        self.assertEqual(start.day, 1)
        self.assertEqual(start.year, today.year)
        self.assertIn(start.month, (1, 4, 7, 10))
        self.assertTrue(0 <= today.month - start.month < 3)

    def test_period_start_date_year(self):
        """Year period starts on the first of January"""
        self.assertEqual(get_period_start_date('year'),
                         date(date.today().year, 1, 1))

    def test_period_start_date_week(self):
        """Week period starts on the Monday of the current week"""
        start = get_period_start_date('week')
        today = date.today()
        self.assertEqual(start.weekday(), 0)
        self.assertEqual(start, today - timedelta(days=today.weekday()))

    def test_period_start_date_invalid(self):
        """An unknown period raises a ValueError"""
        with self.assertRaises(ValueError):
            get_period_start_date('decade')
        with self.assertRaises(ValueError):
            self.Lead.get_data('decade')

    # ------------------------------------------------------------------
    # Dashboard tiles
    # ------------------------------------------------------------------
    def test_get_data_keys(self):
        """get_data returns every tile value used by the dashboard"""
        result = self.Lead.get_data('year')
        self.assertEqual(set(result), {
            'leads', 'opportunities', 'exp_revenue', 'revenue', 'win_ratio',
            'opportunity_ratio', 'avg_close_time', 'unassigned_leads'})

    def test_get_data_counts(self):
        """Newly created leads and opportunities are reflected in the tiles"""
        before = self.Lead.get_data('year')
        self.Lead.create([{
            'name': 'Unassigned Lead',
            'type': 'lead',
            'user_id': False,
        }, {
            'name': 'Assigned Lead',
            'type': 'lead',
            'user_id': self.sales_user.id,
        }, {
            'name': 'Open Opportunity',
            'type': 'opportunity',
            'expected_revenue': 1000,
            'user_id': self.sales_user.id,
        }])
        won = self.Lead.create({
            'name': 'Won Opportunity',
            'type': 'opportunity',
            'expected_revenue': 2000,
            'user_id': self.sales_user.id,
        })
        won.action_set_won()
        after = self.Lead.get_data('year')
        self.assertEqual(after['leads'] - before['leads'], 2)
        self.assertEqual(
            after['unassigned_leads'] - before['unassigned_leads'], 1)
        self.assertEqual(
            after['opportunities'] - before['opportunities'], 2)
        self.assertEqual(after['exp_revenue'] - before['exp_revenue'], 3000)
        self.assertEqual(after['revenue'] - before['revenue'], 2000)

    def test_get_data_avg_close_time(self):
        """Average closing time is returned in days, including the full
        days between creation and conversion"""
        self.Lead.search([('date_conversion', '!=', False)]).write(
            {'date_conversion': False})
        self.assertEqual(self.Lead.get_data('year')['avg_close_time'], 0)
        leads = self.Lead.create([
            {'name': 'Converted Lead 1', 'type': 'opportunity'},
            {'name': 'Converted Lead 2', 'type': 'opportunity'},
        ])
        leads[0].date_conversion = leads[0].create_date + timedelta(days=2)
        leads[1].date_conversion = leads[1].create_date + timedelta(days=3)
        self.assertEqual(self.Lead.get_data('year')['avg_close_time'], 2.5)

    def test_get_data_ratios(self):
        """Win and opportunity ratios count won records against active
        records with zero probability"""
        self.Lead.search([]).action_archive()
        open_opportunities = self.Lead.create([{
            'name': 'Zero Probability Opportunity %s' % i,
            'type': 'opportunity',
            'probability': 0,
        } for i in range(2)])
        won = self.Lead.create({
            'name': 'Ratio Won Opportunity',
            'type': 'opportunity',
        })
        won.action_set_won()
        result = self.Lead.get_data('year')
        self.assertEqual(len(open_opportunities), 2)
        self.assertEqual(result['win_ratio'], 0.5)
        self.assertEqual(result['opportunity_ratio'], 0.5)

    def test_get_crm_activities_without_type(self):
        """Activities without a type are listed with an empty name"""
        lead = self.Lead.create({'name': 'Untyped Activity Lead'})
        activity = self._create_activity(lead, self.sales_user, self.today,
                                         'Untyped')
        self.env.flush_all()
        self.env.cr.execute(
            'UPDATE mail_activity SET activity_type_id = NULL WHERE id = %s',
            (activity.id,))
        counts, names = self.Lead.get_crm_activities('month')
        self.assertIn('', names)
        self.assertGreaterEqual(counts[names.index('')], 1)
        self.Lead.invalidate_model()
        events = self.Lead.with_user(
            self.sales_user).get_upcoming_events()['event']
        self.assertEqual([event[4] for event in events], [''])

    # ------------------------------------------------------------------
    # Charts
    # ------------------------------------------------------------------
    def test_get_lead_stage_data(self):
        """Funnel chart groups the leads by stage name"""
        stage = self.env['crm.stage'].create({'name': 'Dashboard Test Stage'})
        self.Lead.create([
            {'name': 'Stage Lead 1', 'stage_id': stage.id},
            {'name': 'Stage Lead 2', 'stage_id': stage.id},
        ])
        counts, stages = self.Lead.get_lead_stage_data('month')
        self.assertEqual(len(counts), len(stages))
        self.assertIn('Dashboard Test Stage', stages)
        self.assertEqual(counts[stages.index('Dashboard Test Stage')], 2)

    def test_get_lead_by_month(self):
        """Lead by month chart counts the leads of the current month"""
        month_name = calendar.month_name[fields.Datetime.now().month]

        def month_count():
            counts, names = self.Lead.get_lead_by_month()
            return counts[names.index(month_name)] if month_name in names else 0

        before = month_count()
        self.Lead.create([{'name': 'Month Lead 1'}, {'name': 'Month Lead 2'}])
        self.assertEqual(month_count() - before, 2)

    def test_get_crm_activities(self):
        """Activity pie counts the activities by activity type"""
        lead = self.Lead.create({'name': 'Activity Lead'})
        self._create_activity(lead, self.sales_user, self.today, 'Call 1')
        self._create_activity(lead, self.sales_user, self.today, 'Call 2')
        self.env.flush_all()
        counts, names = self.Lead.get_crm_activities('month')
        self.assertIn('Dashboard Test Activity', names)
        self.assertEqual(counts[names.index('Dashboard Test Activity')], 2)

    def test_get_the_campaign_pie(self):
        """Campaign pie counts the leads per campaign"""
        campaign = self.env['utm.campaign'].create(
            {'title': 'Dashboard Test Campaign'})
        self.Lead.create([
            {'name': 'Campaign Lead 1', 'campaign_id': campaign.id},
            {'name': 'Campaign Lead 2', 'campaign_id': campaign.id},
        ])
        self.env.flush_all()
        counts, names = self.Lead.get_the_campaign_pie('month')
        self.assertIn(campaign.name, names)
        self.assertEqual(counts[names.index(campaign.name)], 2)
        self.assertNotIn(None, names)

    def test_get_the_source_pie(self):
        """Source pie counts the leads per source"""
        source = self.env['utm.source'].create(
            {'name': 'Dashboard Test Source'})
        self.Lead.create([
            {'name': 'Source Lead 1', 'source_id': source.id},
            {'name': 'Source Lead 2', 'source_id': source.id},
            {'name': 'Source Lead 3', 'source_id': source.id},
        ])
        self.env.flush_all()
        counts, names = self.Lead.get_the_source_pie('month')
        self.assertIn(source.name, names)
        self.assertEqual(counts[names.index(source.name)], 3)

    def test_get_the_medium_pie(self):
        """Medium pie counts the leads per medium"""
        medium = self.env['utm.medium'].create(
            {'name': 'Dashboard Test Medium'})
        self.Lead.create({'name': 'Medium Lead', 'medium_id': medium.id})
        self.env.flush_all()
        counts, names = self.Lead.get_the_medium_pie('month')
        self.assertIn(medium.name, names)
        self.assertEqual(counts[names.index(medium.name)], 1)

    def test_get_total_lost_crm_months(self):
        """Lost graph returns one entry per month of the period"""
        self.assertEqual(len(self.Lead.get_total_lost_crm('year')['month']),
                         12)
        self.assertEqual(
            len(self.Lead.get_total_lost_crm('quarter')['month']), 3)
        result = self.Lead.get_total_lost_crm('month')
        self.assertEqual(result['month'],
                         [date.today().strftime('%B')])
        self.assertEqual(len(result['month']), len(result['count']))

    def test_get_total_lost_crm_count(self):
        """Lost leads are counted in the month they were created"""
        month_name = fields.Datetime.now().strftime('%B')

        def lost_count():
            self.env.flush_all()
            result = self.Lead.get_total_lost_crm('year')
            return result['count'][result['month'].index(month_name)]

        before = lost_count()
        leads = self.Lead.create([
            {'name': 'Lost Lead 1'}, {'name': 'Lost Lead 2'},
            {'name': 'Open Lead'}])
        leads[:2].action_set_lost()
        self.assertEqual(lost_count() - before, 2)

    def test_total_revenue_by_sales(self):
        """Revenue pie splits the user's revenue into expected, won and
        lost"""
        self.Lead.create({
            'name': 'Active Opportunity',
            'type': 'opportunity',
            'expected_revenue': 1000,
            'user_id': self.sales_user.id,
        })
        won = self.Lead.create({
            'name': 'Won Opportunity',
            'type': 'opportunity',
            'expected_revenue': 300,
            'user_id': self.sales_user.id,
        })
        won.action_set_won()
        lost = self.Lead.create({
            'name': 'Lost Opportunity',
            'type': 'opportunity',
            'expected_revenue': 400,
            'user_id': self.sales_user.id,
        })
        lost.action_set_lost()
        # Opportunities of another user must not be counted
        self.Lead.create({
            'name': 'Other Opportunity',
            'type': 'opportunity',
            'expected_revenue': 5000,
            'user_id': self.other_user.id,
        })
        self.env.flush_all()
        counts, titles = self.Lead.with_user(
            self.sales_user).total_revenue_by_sales('month')
        self.assertEqual(titles, ['Expected without Won', 'Won', 'Lost'])
        self.assertEqual(counts, [1000, 300, 400])

    def test_total_revenue_by_sales_empty(self):
        """Revenue pie is zero for a user without opportunities"""
        self.env.flush_all()
        counts, _titles = self.Lead.with_user(
            self.sales_user).total_revenue_by_sales('month')
        self.assertEqual(counts, [0, 0, 0])

    # ------------------------------------------------------------------
    # Tables
    # ------------------------------------------------------------------
    def test_get_top_sp_revenue(self):
        """Top revenue table lists at most 10 leads of the user"""
        self.Lead.create([{
            'name': 'Revenue Lead %s' % i,
            'type': 'opportunity',
            'expected_revenue': i * 100,
            'user_id': self.sales_user.id,
        } for i in range(1, 13)])
        self.Lead.create({
            'name': 'Other Revenue Lead',
            'type': 'opportunity',
            'expected_revenue': 999999,
            'user_id': self.other_user.id,
        })
        self.env.flush_all()
        rows = self.Lead.with_user(
            self.sales_user).get_top_sp_revenue('month')['top_revenue']
        self.assertEqual(len(rows), 10)
        self.assertEqual([row[2] for row in rows],
                         [i * 100 for i in range(12, 2, -1)])
        self.assertTrue(all(row[0] == self.sales_user.name for row in rows))
        self.assertEqual(rows[0][3], 'Revenue Lead 12')
        self.assertEqual(rows[0][4], self.env.company.currency_id.symbol)

    def test_get_top_country_revenue(self):
        """Country revenue table is ordered by expected revenue"""
        country = self.env.ref('base.aq')
        self.Lead.create({
            'name': 'Country Revenue Lead',
            'country_id': country.id,
            'expected_revenue': 10 ** 12,
        })
        self.env.flush_all()
        rows = self.Lead.get_top_country_revenue('month')['country_revenue']
        self.assertLessEqual(len(rows), 10)
        self.assertEqual(rows[0][0], country.name)
        self.assertEqual(rows[0][1], 10 ** 12)
        self.assertEqual(rows[0][2], self.env.company.currency_id.symbol)

    def test_get_top_country_count(self):
        """Country count table is ordered by number of leads"""
        country = self.env.ref('base.aq')
        self.Lead.create([{
            'name': 'Country Count Lead %s' % i,
            'country_id': country.id,
        } for i in range(100)])
        self.env.flush_all()
        rows = self.Lead.get_top_country_count('month')['country_count']
        self.assertLessEqual(len(rows), 10)
        self.assertEqual(rows[0][0], country.name)
        self.assertGreaterEqual(rows[0][1], 100)

    def test_get_upcoming_events(self):
        """Upcoming activities only show future activities of the user"""
        lead = self.Lead.create({'name': 'Upcoming Lead'})
        self._create_activity(lead, self.sales_user,
                              self.today + timedelta(days=3), 'Future Call')
        self._create_activity(lead, self.sales_user,
                              self.today - timedelta(days=3), 'Past Call')
        self._create_activity(lead, self.other_user,
                              self.today + timedelta(days=3), 'Other Call')
        self.env.flush_all()
        result = self.Lead.with_user(self.sales_user).get_upcoming_events()
        summaries = [event[2] for event in result['event']]
        self.assertEqual(summaries, ['Future Call'])
        event = result['event'][0]
        self.assertEqual(event[0], self.activity_type.id)
        self.assertEqual(event[3], lead.name)
        self.assertEqual(event[4], 'Dashboard Test Activity')
        self.assertEqual(event[5], self.sales_user.name)

    def test_get_recent_activities_user(self):
        """Recent activities of a salesperson only show their own activities
        of the last week"""
        lead = self.Lead.create({'name': 'Recent Lead'})
        self._create_activity(lead, self.sales_user,
                              self.today - timedelta(days=2), 'Recent Call')
        self._create_activity(lead, self.sales_user,
                              self.today - timedelta(days=10), 'Old Call')
        self._create_activity(lead, self.other_user,
                              self.today - timedelta(days=2), 'Other Call')
        self.env.flush_all()
        result = self.Lead.with_user(
            self.sales_user).get_recent_activities()
        summaries = [activity[2] for activity in result['activities']]
        self.assertEqual(summaries, ['Recent Call'])
        self.assertEqual(result['activities'][0][4],
                         'Dashboard Test Activity')
        self.assertEqual(result['activities'][0][5], self.sales_user.name)

    def test_get_recent_activities_admin(self):
        """Recent activities of an administrator show every user's
        activities"""
        lead = self.Lead.create({'name': 'Recent Admin Lead'})
        self._create_activity(lead, self.sales_user,
                              self.today - timedelta(days=1), 'Sales Call')
        self._create_activity(lead, self.other_user,
                              self.today - timedelta(days=1), 'Other Call')
        self.env.flush_all()
        result = self.Lead.with_user(
            self.admin_user).get_recent_activities()
        summaries = [activity[2] for activity in result['activities']]
        self.assertIn('Sales Call', summaries)
        self.assertIn('Other Call', summaries)
