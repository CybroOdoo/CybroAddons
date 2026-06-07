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
from odoo import fields, models


class View(models.Model):
    """Add the `map` view type to `ir.ui.view` and register its UI metadata."""

    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=[('map', 'Map')])

    def _is_qweb_based_view(self, view_type):
        """Return whether `view_type` is rendered via QWeb/Owl."""
        return view_type == "map" or super()._is_qweb_based_view(view_type)

    def _get_view_info(self):
        """Register the `map` view icon in the view switcher."""
        return {
            'map': {'icon': 'fa fa-map-marker'}} | super()._get_view_info()


class ActWindowView(models.Model):
    """Allow `map` in window action view modes."""

    _inherit = 'ir.actions.act_window.view'

    view_mode = fields.Selection(selection_add=[('map', 'Map')], ondelete={'map': 'cascade'})
