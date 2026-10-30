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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestUtmCampaignRatio(TransactionCase):
    """Test cases for the win loss ratio smart button on utm.campaign and the
    salesperson target on res.users"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sales_user = cls.env['res.users'].create({
            'name': 'Dashboard Ratio Salesperson',
            'login': 'crm_dashboard_ratio_salesperson',
            'email': 'crm_dashboard_ratio@example.com',
            'group_ids': [(6, 0, [
                cls.env.ref('sales_team.group_sale_salesman').id])],
        })
        cls.campaign = cls.env['utm.campaign'].create(
            {'title': 'Dashboard Ratio Campaign'})

    def _create_leads(self, count, campaign=None):
        """Create opportunities linked to the given campaign"""
        campaign = campaign or self.campaign
        return self.env['crm.lead'].create([{
            'name': 'Ratio Lead %s' % i,
            'type': 'opportunity',
            'user_id': self.sales_user.id,
            'campaign_id': campaign.id,
        } for i in range(count)])

    def _get_ratio(self, campaign=None):
        """Return the freshly computed ratio of the campaign"""
        campaign = campaign or self.campaign
        campaign.invalidate_recordset(['total_ratio'])
        return campaign.total_ratio

    def test_ratio_without_lost_leads(self):
        """The ratio is zero when the campaign has no lost leads"""
        self._create_leads(2).action_set_won()
        self.assertEqual(self._get_ratio(), 0)

    def test_ratio_won_and_lost(self):
        """The ratio is the number of won leads over the lost leads"""
        self._create_leads(4).action_set_won()
        self._create_leads(3).action_set_lost()
        self.assertEqual(self._get_ratio(), round(4 / 3, 2))

    def test_ratio_per_campaign(self):
        """Each campaign only counts its own leads"""
        other_campaign = self.env['utm.campaign'].create(
            {'title': 'Dashboard Other Campaign'})
        self._create_leads(1).action_set_won()
        self._create_leads(2).action_set_lost()
        self._create_leads(3, other_campaign).action_set_won()
        self._create_leads(1, other_campaign).action_set_lost()
        self.assertEqual(self._get_ratio(), 0.5)
        self.assertEqual(self._get_ratio(other_campaign), 3)
        campaigns = self.campaign | other_campaign
        campaigns.invalidate_recordset(['total_ratio'])
        self.assertEqual(campaigns.mapped('total_ratio'), [0.5, 3])

    def test_get_ratio_action(self):
        """The smart button opens the won and lost leads of the campaign"""
        action = self.campaign.get_ratio()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'crm.lead')
        self.assertEqual(action['view_mode'], 'kanban')
        self.assertEqual(action['domain'][0],
                         ['campaign_id', '=', self.campaign.id])
        won = self._create_leads(1)
        won.action_set_won()
        lost = self._create_leads(1)
        lost.action_set_lost()
        open_lead = self._create_leads(1)
        other_won = self._create_leads(1, self.env['utm.campaign'].create(
            {'title': 'Dashboard Unrelated Campaign'}))
        other_won.action_set_won()
        found = self.env['crm.lead'].with_context(active_test=False).search(
            action['domain'])
        self.assertIn(won, found)
        self.assertIn(lost, found)
        self.assertNotIn(open_lead, found)
        self.assertNotIn(other_won, found)

    def test_user_sales_target(self):
        """The salesperson target is stored on the user"""
        self.sales_user.sales = 25000
        self.assertEqual(self.sales_user.sales, 25000)
