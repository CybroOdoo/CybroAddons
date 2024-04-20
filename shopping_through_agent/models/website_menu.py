# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ashok PK (odoo@cybrosys.com)
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
###############################################################################
from odoo import models


class WebsiteMenu(models.Model):
    """Class to add a function for menu visibility"""
    _inherit = 'website.menu'

    def _compute_visible(self):
        """Compute menu invisible for customer and visible for agent"""
        super()._compute_visible()
        self.env.registry._clear_cache()
        for menu in self:
            visible = True
            if menu.name == 'Agent Shop':
                if not menu.env.user.partner_id.is_agent:
                    visible = False
            menu.is_visible = visible
