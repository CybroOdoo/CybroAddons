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
from odoo import models


class WebsiteMenu(models.Model):
    """ Adding website menu"""
    _inherit = "website.menu"

    def _compute_visible(self):
        """Make the 'Sell' menu visible on the website based on the setting
        done from backend"""
        super()._compute_visible()
        show_sell_menu_header = self.env[
            'ir.config_parameter'].sudo().get_param(
            'multi_vendor_marketplace.show_sell_menu_header')
        for menu in self:
            if menu.url == '/sell':
                menu.is_visible = bool(show_sell_menu_header)
