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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Test suite for POS session loading product product."""
from unittest.mock import patch
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosSession(TransactionCase):
    """Test pos.session product loading functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test Session POS',
            'module_pos_restaurant': True,
        })
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
            'user_id': cls.env.user.id,
        })
        cls.booking_product = cls.env.ref(
            'table_reservation_on_website.product_product_table_booking_pos')

    def test_get_pos_ui_product_product_append(self):
        """Test _get_pos_ui_product_product when product is not yet in result."""
        params = {'search_params': {'fields': ['id', 'name', 'display_name', 'lst_price']}}
        with patch('odoo.addons.point_of_sale.models.pos_session.PosSession._get_pos_ui_product_product', create=True, return_value=[]):
            res = self.pos_session._get_pos_ui_product_product(params)
            self.assertTrue(any(p['id'] == self.booking_product.id for p in res))
            booking_item = next(p for p in res if p['id'] == self.booking_product.id)
            self.assertIn('categ', booking_item)
            self.assertEqual(booking_item['categ']['id'], self.booking_product.categ_id.id)

    def test_get_pos_ui_product_product_already_loaded(self):
        """Test _get_pos_ui_product_product when product is already loaded in result."""
        existing_result = [{'id': self.booking_product.id, 'name': 'Table Booking[POS]'}]
        params = {'search_params': {'fields': ['id', 'name']}}
        with patch('odoo.addons.point_of_sale.models.pos_session.PosSession._get_pos_ui_product_product', create=True, return_value=existing_result):
            res = self.pos_session._get_pos_ui_product_product(params)
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]['id'], self.booking_product.id)

