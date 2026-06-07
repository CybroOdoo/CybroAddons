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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestIrUiView(TransactionCase):

    def test_01_view_type_selection(self):
        """Test that 'map' is added to the selection of view types."""
        selection = self.env['ir.ui.view']._fields['type'].selection
        self.assertIn(('map', 'Map'), selection)

    def test_02_is_qweb_based_view(self):
        """Test _is_qweb_based_view for map view type."""
        is_qweb = self.env['ir.ui.view']._is_qweb_based_view('map')
        self.assertTrue(is_qweb)
        
        # Test default fallback
        is_qweb_kanban = self.env['ir.ui.view']._is_qweb_based_view('kanban')
        self.assertTrue(is_qweb_kanban)

    def test_03_get_view_info(self):
        """Test _get_view_info returns the icon configuration for map view."""
        info = self.env['ir.ui.view']._get_view_info()
        self.assertIn('map', info)
        self.assertEqual(info['map'].get('icon'), 'fa fa-map-marker')

    def test_04_act_window_view_mode_selection(self):
        """Test that 'map' is added to the selection of window action view modes."""
        selection = self.env['ir.actions.act_window.view']._fields['view_mode'].selection
        self.assertIn(('map', 'Map'), selection)
