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
from odoo import models

HELPDESK_URL = '/helpdesk_ticket'


class WebsiteMenu(models.Model):
    """Show the Helpdesk menu of the website when it is enabled in the
    settings"""
    _inherit = "website.menu"

    def _compute_visible(self):
        """Hide the Helpdesk menu when it is disabled in the settings"""
        result = super()._compute_visible()
        show_menu = self.env['ir.config_parameter'].sudo().get_bool(
            'odoo_website_helpdesk.helpdesk_menu_show')
        for menu in self.filtered(lambda menu: menu.url == HELPDESK_URL):
            menu.is_visible = show_menu
        return result
