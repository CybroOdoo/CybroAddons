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
from odoo.tests.common import TransactionCase

class TestIrUiView(TransactionCase):
    
    def test_01_is_qweb_based_view(self):
        """ Test if 'map' view is recognized as qweb based """
        self.assertTrue(self.env['ir.ui.view']._is_qweb_based_view('map'))
        self.assertFalse(self.env['ir.ui.view']._is_qweb_based_view('form')) # form is not qweb based in standard check

    def test_02_get_view_info(self):
        """ Test if 'map' view icon is added to view info """
        view_info = self.env['ir.ui.view']._get_view_info()
        self.assertIn('map', view_info)
        self.assertEqual(view_info['map']['icon'], 'fa fa-map-marker')

class TestActWindowView(TransactionCase):

    def setUp(self):
        super().setUp()
        self.action = self.env['ir.actions.act_window'].create({
            'name': 'Test Action',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
        })
    
    def test_01_act_window_map_view(self):
        """ Test creating an act_window_view with mode 'map' """
        view = self.env['ir.actions.act_window.view'].create({
            'act_window_id': self.action.id,
            'view_mode': 'map',
            'sequence': 10,
        })
        self.assertEqual(view.view_mode, 'map')
