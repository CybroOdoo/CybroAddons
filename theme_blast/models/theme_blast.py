# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models


class ThemeBlast(models.AbstractModel):
    _inherit = 'theme.utils'

    def _theme_blast_post_copy(self, mod):
        """Reinitialize templates"""
        self.disable_view('website.placeholder_header_call_to_action')
        self.enable_view('website.template_header_default_align_right')
        self.enable_header_off_canvas()


class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    def _theme_load(self, website):
        """Load snippets"""
        res = super()._theme_load(website)
        homepage = website.homepage_id
        if homepage:
            homepage.header_overlay = True
        return res
