"""Module that allows to custom robots.txt """
# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Renu M (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models, api


class Robots(models.TransientModel):
    """Module that allows to custom robots.txt """
    _inherit = "website.robots"

    mode = fields.Selection([('custom', 'Custom'), ('allow_all', 'Allow All'),
                             ('disallow_all', 'Disallow All')],
                            default=lambda s: s.env[
                                'website'].get_current_website().mode,
                            help="Select mode of the robots.txt file that helps you in indexing")

    @api.onchange('mode')
    def _onchange_mode(self):
        """Adding data according to the change of mode"""
        if not self.env['website'].get_current_website().robots_txt:
            if self.mode == 'custom':
                self.content = " "
            else:
                self.content = self.env[
                    'website'].get_current_website().robots_txt
        if self.mode == 'allow_all':
            self.content = """User-agent: *
            Allow: /"""
        if self.mode == 'disallow_all':
            self.content = """User-agent: *
            Disallow: /"""

    def action_save(self):
        """Supering the action save"""
        res = super(Robots, self).action_save()
        self.env['website'].get_current_website().mode = self.mode
        self.env['website'].get_current_website().robots_txt = self.content
        return res
