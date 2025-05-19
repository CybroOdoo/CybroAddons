# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    """
     Inheriting the website menu.

     This class inherits from the 'website.menu' model and extends its
     functionality to compute the visibility of the menu
     item based on the value of the 'odoo_website_helpdesk.helpdesk_menu_show'
     configuration parameter.

     Attributes:
        _inherit (str): The name of the model being inherited.
    """
    _inherit = "website.menu"

    def _compute_visible(self):
        """
        Compute the visibility of the menu item.

        This method is used to determine whether the menu item should be
        visible or hidden based on the value of the
        'odoo_website_helpdesk.helpdesk_menu_show' configuration parameter.

        Returns:
            None

        Side Effects:
            Sets the 'is_visible' field of the menu item record to True or
            False accordingly.
        """
        super()._compute_visible()
        show_menu_header = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_website_helpdesk.helpdesk_menu_show')
        for menu in self:
            if menu.name == 'Helpdesk' and show_menu_header is False:
                menu.is_visible = False
            if menu.name == 'Helpdesk' and show_menu_header is True:
                menu.is_visible = True
