# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Megha A P (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestMenuItemDraggable(TransactionCase):

    def setUp(self):
        super(TestMenuItemDraggable, self).setUp()
        self.menu_item_draggable = self.env['menu.item.draggable']
        self.parent_menu = self.env['ir.ui.menu'].create({
            'name': 'Test Parent Menu',
            'sequence': 10,
        })
        self.menu_1 = self.env['ir.ui.menu'].create({
            'name': 'Test Menu 1',
            'sequence': 1,
            'parent_id': self.parent_menu.id,
        })
        self.menu_2 = self.env['ir.ui.menu'].create({
            'name': 'Test Menu 2',
            'sequence': 2,
            'parent_id': self.parent_menu.id,
        })
        self.menu_3 = self.env['ir.ui.menu'].create({
            'name': 'Test Menu 3',
            'sequence': 3,
            'parent_id': self.parent_menu.id,
        })

    def test_get_menu_item(self):
        inner_text = ['Test Menu 3', 'Test Menu 1', 'Test Menu 2']
        self.menu_item_draggable.with_context(**{'ir.ui.menu.full_list': True}).get_menu_item(self.menu_1.id, inner_text)
        self.assertEqual(self.menu_3.sequence, 1)
        self.assertEqual(self.menu_1.sequence, 2)
        self.assertEqual(self.menu_2.sequence, 3)
