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
from odoo.tools import BinaryBytes, file_open


class ThemeUtils(models.AbstractModel):
    """Set the DriveX header and footer defaults on theme install."""
    _inherit = 'theme.utils'

    def _theme_drivex_post_copy(self, mod):
        """Configure the standard header/footer the way DriveX is designed.

        Everything set here stays editable from the website builder.
        """
        self.enable_view('website.template_header_default')
        self.enable_view('website.template_header_default_align_center')
        self.enable_view('website.footer_custom')
        self.enable_view('website.header_visibility_fixed')
        self.disable_view('website.header_search_box')
        self.disable_view('website.header_text_element')
        self.disable_view('website.header_call_to_action')
        with file_open('theme_drivex/static/src/img/logo.svg', 'rb') as logo:
            self.env.website.logo = BinaryBytes(logo.read())
