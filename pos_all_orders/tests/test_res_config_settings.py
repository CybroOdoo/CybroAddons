# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):

    def setUp(self):
        super().setUp()
        self.params = self.env['ir.config_parameter'].sudo()

    def test_get_values_returns_pos_all_orders_parameters(self):
        self.params.set_param('pos_all_orders.pos_all_order', 'past_order')
        self.params.set_param('pos_all_orders.n_days', 7)

        values = self.env['res.config.settings'].get_values()

        self.assertEqual(values['pos_all_order'], 'past_order')
        self.assertEqual(values['n_days'], '7')

    def test_set_values_stores_pos_all_orders_parameters(self):
        settings = self.env['res.config.settings'].create({
            'pos_all_order': 'last_n',
            'n_days': 15,
        })

        settings.set_values()

        self.assertEqual(
            self.params.get_param('pos_all_orders.pos_all_order'),
            'last_n',
        )
        self.assertEqual(
            self.params.get_param('pos_all_orders.n_days'),
            '15',
        )
