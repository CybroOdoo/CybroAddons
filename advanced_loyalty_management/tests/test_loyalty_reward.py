# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase


class TestLoyaltyReward(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loyalty_program = cls.env['loyalty.program'].create({
            'name': 'Test Program',
            'program_type': 'loyalty',
            'applies_on': 'both',
        })
        cls.reward = cls.env['loyalty.reward'].create({
            'program_id': cls.loyalty_program.id,
            'reward_type': 'redemption',
            'redemption_amount': 2.0,
            'max_redemption_type': 'percent',
            'max_redemption_amount': 20.0,
            'redemption_frequency': 2,
            'redemption_frequency_unit': 'week',
            'redemption_eligibility': 100.0,
        })

    def test_reward_fields_and_description(self):
        """Test that the reward fields and compute description work."""
        self.assertEqual(self.reward.reward_type, 'redemption')
        self.assertEqual(self.reward.redemption_amount, 2.0)
        self.assertEqual(self.reward.max_redemption_type, 'percent')
        
        # Test description compute method
        self.assertEqual(self.reward.description, 'Redemption')
        
    def test_load_pos_data_fields(self):
        """Test custom pos load fields."""
        fields = self.env['loyalty.reward']._load_pos_data_fields(None)
        self.assertIn('redemption_point', fields)
        self.assertIn('redemption_amount', fields)
        self.assertIn('max_redemption_amount', fields)
