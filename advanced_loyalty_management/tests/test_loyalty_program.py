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


class TestLoyaltyProgram(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.loyalty_program = cls.env['loyalty.program'].create({
            'name': 'Test Program',
            'program_type': 'loyalty',
            'applies_on': 'both',
        })

    def test_convert_loyalty_new_card(self):
        """Test creating a new loyalty card with points when negative CID is provided."""
        self.env['loyalty.program'].convert_loyalty(
            pid=[self.loyalty_program.id],
            cid=['-1'],
            loyalty=[50.0],
            partner_id=[self.partner.id]
        )
        card = self.env['loyalty.card'].search([
            ('partner_id', '=', self.partner.id),
            ('program_id', '=', self.loyalty_program.id)
        ])
        self.assertTrue(card)
        self.assertEqual(card.points, 50.0)

    def test_convert_loyalty_existing_card(self):
        """Test adding points to an existing loyalty card."""
        card = self.env['loyalty.card'].create({
            'partner_id': self.partner.id,
            'program_id': self.loyalty_program.id,
            'points': 20.0
        })
        self.env['loyalty.program'].convert_loyalty(
            pid=[self.loyalty_program.id],
            cid=[str(card.id)],
            loyalty=[30.0],
            partner_id=[self.partner.id]
        )
        self.assertEqual(card.points, 50.0)

    def test_load_pos_data_fields(self):
        """Test that custom fields are added to pos data load."""
        fields = self.env['loyalty.program']._load_pos_data_fields(None)
        self.assertIn('point_rate', fields)
        self.assertIn('change_rate', fields)
