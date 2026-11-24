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
from odoo import models


class ThemeWebsiteMenu(models.Model):
    """Keep the link of the theme menus that are not tied to a page."""
    _inherit = 'theme.website.menu'

    def _convert_to_base_model(self, website, **kwargs):
        """Store the URL of a menu without page as its manual URL.

        A menu follows its page, and the theme copy writes an empty page on
        the menu each time the theme is loaded or updated, which turns the
        link of a menu such as Contact into ``#`` (it stays on the current
        page). The manual URL is the link used whenever there is no page.
        """
        values = super()._convert_to_base_model(website, **kwargs)
        if values and not values.get('page_id') and self.url \
                and self.url != '#' and '#' not in self.url:
            values['manual_url'] = self.url
        return values
