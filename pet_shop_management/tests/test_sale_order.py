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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'pet_shop_management')
class TestSaleOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Sale Order Customer',
        })
        cls.walker = cls.env['hr.employee'].create({
            'name': 'Walker John',
            'is_walker_sitters': True,
        })
        cls.service = cls.env['product.product'].create({
            'name': 'Pet Sitting Service',
            'is_pet_service': True,
            'list_price': 50.0,
        })

    def test_01_pet_sitting_action_and_context(self):
        """ Test pet_sitting wizard action from sale order """
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [Command.create({
                'product_id': self.service.id,
                'walker_sitting': self.walker.id,
                'price_unit': 50.0,
            })],
        })

        self.assertFalse(order.pet_sittings)

        action = order.pet_sitting()
        self.assertTrue(order.pet_sittings)
        self.assertEqual(action.get('res_model'), 'pet.sitting.schedule')
        self.assertEqual(action.get('target'), 'new')
        ctx = action.get('context', {})
        self.assertNotIn('default_model_id', ctx)
        self.assertEqual(ctx.get('default_reference_id'), order.id)
        self.assertEqual(ctx.get('default_schedule_description'), order.name)
        self.assertEqual(ctx.get('default_walker_sitting_id'), self.walker.id)

    def test_02_action_return_meetings(self):
        """ Test action_return_meetings action """
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        action = order.action_return_meetings()
        self.assertEqual(action.get('res_model'), 'sitting.schedule')
        self.assertEqual(action.get('view_mode'), 'calendar,list,form')
        self.assertEqual(action.get('domain'), [('number_id', '=', order.id)])
        self.assertEqual(
            action.get('context', {}).get('default_number_id'), order.id
        )
