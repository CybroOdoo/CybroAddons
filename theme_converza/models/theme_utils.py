# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models


class ThemeUtils(models.AbstractModel):
    """Hooks run when the theme is applied to a website."""
    _inherit = 'theme.utils'

    def _theme_converza_post_copy(self, mod):
        """Use the Converza header instead of the default header template.

        Both templates replace the navigation bar of the standard header, so
        only one of them can be active. Everything around the navigation
        bar (header options, visibility, anchors) stays the standard one.
        """
        self.disable_view('website.template_header_default')
        self.enable_view('theme_converza.converza_header_layout')
