# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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


class TestResUsers(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = cls.env['res.users'].sudo().create({
            'name': 'User Filter Test',
            'login': 'user-filter-test@example.com',
            'email': 'user-filter-test@example.com',
            'group_ids': [(4, cls.env.ref('base.group_user').id)],
        })

    def test_get_views_updates_filter_booleans_from_user_groups(self):
        self.test_user.write({
            'sales_user': True,
            'invoice_user': True,
            'purchase_user': True,
            'website_user': True,
            'inventory_user': True,
            'pos_user': True,
            'project_user': True,
            'manufacturing_user': True,
        })

        self.env['res.users'].get_views([])

        self.assertFalse(self.test_user.sales_user)
        self.assertFalse(self.test_user.invoice_user)
        self.assertFalse(self.test_user.purchase_user)
        self.assertFalse(self.test_user.website_user)
        self.assertFalse(self.test_user.inventory_user)
        self.assertFalse(self.test_user.pos_user)
        self.assertFalse(self.test_user.project_user)
        self.assertFalse(self.test_user.manufacturing_user)

    def test_user_search_view_contains_filter_fields(self):
        search_view = self.env.ref('partner_related_user.view_users_search')

        self.env['res.users'].get_views(
            [(search_view.id, 'search')],
            {'toolbar': False},
        )

        for field_name in [
            'sales_user',
            'invoice_user',
            'purchase_user',
            'website_user',
            'inventory_user',
            'pos_user',
            'project_user',
            'manufacturing_user',
        ]:
            self.assertIn(field_name, self.env['res.users']._fields)
            self.assertIn(field_name, search_view.arch_db)
