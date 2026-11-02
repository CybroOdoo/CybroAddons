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
from odoo import Command
from odoo.tests import tagged
from odoo.addons.point_of_sale.tests.test_frontend import TestPointOfSaleHttpCommon


@tagged('post_install', '-at_install')
class TestAdvancedLoyaltyFrontend(TestPointOfSaleHttpCommon):
    """Frontend tour tests for advanced loyalty management."""

    def test_pos_advanced_loyalty_tour(self):
        """Test redemption reward in POS interface via frontend tour."""
        partner = self.env['res.partner'].create({'name': 'Loyalty Test Customer'})
        self.whiteboard_pen.product_variant_ids.write({'lst_price': 20})
        self.main_pos_config.write({
            'tax_regime_selection': False,
            'use_pricelist': False,
        })
        self.main_pos_config.with_user(self.pos_user).open_ui()
        program = self.env['loyalty.program'].create({
            'name': 'Test Redemption Program',
            'program_type': 'loyalty',
            'trigger': 'auto',
            'applies_on': 'both',
            'point_rate': 1,
            'rule_ids': [Command.create({
                'reward_point_amount': 1,
                'reward_point_mode': 'money',
                'minimum_qty': 1,
            })],
            'reward_ids': [Command.create({
                'reward_type': 'redemption',
                'redemption_amount': 1.0,
                'max_redemption_type': 'amount',
                'max_redemption_amount': 10.0,
                'redemption_frequency': 5,
                'redemption_frequency_unit': 'day',
                'redemption_eligibility': 10.0,
            })],
        })
        self.env['loyalty.card'].create({
            'program_id': program.id,
            'partner_id': partner.id,
            'points': 50.0,
        })
        self.start_pos_tour("AdvancedLoyaltyTour")
