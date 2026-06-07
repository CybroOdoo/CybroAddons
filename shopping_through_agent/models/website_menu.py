# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo import models


class WebsiteMenu(models.Model):
    """Class to add a function for menu visibility"""
    _inherit = 'website.menu'

    def _compute_visible(self):
        """Compute menu invisible for customer and visible for agent"""
        super()._compute_visible()
        self.env.registry.clear_cache('templates')
        for menu in self:
            visible = True
            if menu.name == 'Agent Shop':
                if not menu.env.user.partner_id.is_agent:
                    visible = False
            menu.is_visible = visible
