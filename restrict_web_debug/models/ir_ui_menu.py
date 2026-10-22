# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, models


class IrUiMenu(models.Model):
    """Inherits the model ir.ui.menu to ensure technical menus are not loaded
    for users in restrict_debug_mode"""
    _inherit = 'ir.ui.menu'

    def load_web_menus(self, debug):
        if self.env.user.has_group('restrict_web_debug.restrict_debug_mode'):
            debug = False
        return super().load_web_menus(debug)

    @api.model
    def _visible_menu_ids(self, debug=False):
        if self.env.user.has_group('restrict_web_debug.restrict_debug_mode'):
            debug = False
        return super()._visible_menu_ids(debug=debug)
