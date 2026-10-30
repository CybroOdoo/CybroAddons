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
class TestSaleOrderCrmStage(TransactionCase):
    """Test cases for moving the opportunity stage on sale order
    confirmation"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create(
            {'name': 'Dashboard Customer'})
        cls.product = cls.env['product.product'].create({
            'name': 'Dashboard Product',
            'list_price': 100,
        })
        cls.initial_stage = cls.env['crm.stage'].create({
            'name': 'Dashboard Initial Stage',
            'sequence': 1,
        })
        cls.confirmed_stage = cls.env['crm.stage'].create({
            'name': 'Dashboard Confirmed Stage',
            'sequence': 50,
        })
        cls.team = cls.env['crm.team'].create({
            'name': 'Dashboard Sales Team',
            'crm_lead_state_id': cls.confirmed_stage.id,
        })

    def _create_order(self, opportunity=False):
        """Create a sale order with one line for the given opportunity"""
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'opportunity_id': opportunity.id if opportunity else False,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
            })],
        })

    def test_team_crm_lead_state(self):
        """The sales team stores the stage used on order confirmation"""
        self.assertEqual(self.team.crm_lead_state_id, self.confirmed_stage)

    def test_confirm_moves_opportunity_stage(self):
        """Confirming the order moves the opportunity to the team stage"""
        opportunity = self.env['crm.lead'].create({
            'name': 'Dashboard Opportunity',
            'type': 'opportunity',
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'stage_id': self.initial_stage.id,
        })
        order = self._create_order(opportunity)
        self.assertEqual(opportunity.stage_id, self.initial_stage)
        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        self.assertEqual(opportunity.stage_id, self.confirmed_stage)

    def test_confirm_team_without_stage(self):
        """The opportunity keeps its stage when the team has no stage set"""
        self.team.crm_lead_state_id = False
        opportunity = self.env['crm.lead'].create({
            'name': 'Dashboard Opportunity No Stage',
            'type': 'opportunity',
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'stage_id': self.initial_stage.id,
        })
        self._create_order(opportunity).action_confirm()
        self.assertEqual(opportunity.stage_id, self.initial_stage)

    def test_confirm_without_opportunity(self):
        """Confirming an order without an opportunity still works"""
        order = self._create_order()
        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        self.assertFalse(order.opportunity_id)
