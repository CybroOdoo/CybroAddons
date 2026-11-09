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
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestHideMenuTour(HttpCase):
    """Run the favourites and app order features in the web client."""

    def test_favorites_and_app_order_tour(self):
        admin = self.env.ref('base.user_admin')
        apps = self.env['ir.ui.menu'].with_user(admin).load_menus(False)['root']['children']
        self.start_tour('/odoo/action-base.action_res_users',
                        'hide_menu_user_favorites_and_app_order', login='admin')
        favorites = self.env['hide.menu.favorite'].search([('user_id', '=', admin.id)])
        self.assertEqual(len(favorites), 2)
        settings = admin.res_users_settings_ids
        self.assertEqual(settings.hide_menu_app_order[:2], [apps[1], apps[0]])
