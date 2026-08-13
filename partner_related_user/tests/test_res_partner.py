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


class TestResPartner(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = cls.env['res.users'].sudo().create({
            'name': 'Partner Related User Test',
            'login': 'partner-related-user-test@example.com',
            'email': 'partner-related-user-test@example.com',
            'group_ids': [(4, cls.env.ref('base.group_user').id)],
        })

    def test_get_views_sets_related_user_on_user_partner(self):
        partner = self.test_user.partner_id
        partner.write({
            'related_user_id': False,
            'is_have_user': False,
        })

        self.env['res.partner'].get_views([])

        self.assertEqual(partner.related_user_id, self.test_user)
        self.assertTrue(partner.is_have_user)

    def test_partner_search_view_contains_related_user_fields(self):
        search_view = self.env.ref(
            'partner_related_user.view_res_partner_filter'
        )

        self.env['res.partner'].get_views(
            [(search_view.id, 'search')],
            {'toolbar': False},
        )

        self.assertIn('related_user_id', self.env['res.partner']._fields)
        self.assertIn('is_have_user', self.env['res.partner']._fields)
        self.assertIn('related_user_id', search_view.arch_db)
        self.assertIn('is_have_user', search_view.arch_db)
