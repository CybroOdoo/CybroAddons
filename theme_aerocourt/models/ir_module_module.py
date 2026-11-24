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


class IrModuleModule(models.Model):
    """Resolve the AeroCourt placeholders each time the theme is loaded."""
    _inherit = 'ir.module.module'

    def _theme_load(self, website):
        """Replace the placeholders of the AeroCourt views after a theme load.

        A theme update copies the theme views on the website again without
        calling the post copy hook, so the placeholders of the views it
        rewrites would stay unresolved.

        :param website: the website the themes are loaded on.
        """
        result = super()._theme_load(website)
        if 'theme_aerocourt' in self.mapped('name'):
            self.env['theme.utils'].with_context(
                website_id=website.id)._aerocourt_resolve_placeholders(website)
        return result
