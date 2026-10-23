# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#############################################################################
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestPosMassEditTour(HttpCase):
    """Browser tests for the mass edit popup of the POS."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Mass Edit Test Product',
            'type': 'consu',
            'available_in_pos': True,
            'list_price': 10.0,
            'taxes_id': [(5, 0, 0)],
        })

    def _open_pos_and_run(self, tour_name, **config_vals):
        """Create a POS, open a session and run the tour as admin."""
        config = self.env['pos.config'].create({
            'name': 'Mass Edit Tour POS',
            'manual_discount': True,
            **config_vals,
        })
        config.with_user(self.env.ref('base.user_admin')).open_ui()
        self.start_tour(
            "/pos/ui?config_id=%d" % config.id, tour_name, login='admin')

    def test_mass_edit_popup_edit_delete_and_undo(self):
        """Quantity, price and discount edits reach the order line, a
        deleted line can be restored with Undo Delete."""
        self._open_pos_and_run('PosMassEditPopupTour')

    def test_mass_edit_empty_order_shows_alert(self):
        """With no order line an alert is shown instead of the popup."""
        self._open_pos_and_run('PosMassEditEmptyOrderTour')

    def test_mass_edit_button_hidden_when_disabled(self):
        """show_mass_edit_button=False hides the Edit Order Line button."""
        self._open_pos_and_run(
            'PosMassEditButtonHiddenTour', show_mass_edit_button=False)
