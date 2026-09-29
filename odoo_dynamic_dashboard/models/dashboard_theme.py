# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.info)
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
###############################################################################
from odoo import api, fields, models


class DashboardTheme(models.Model):
    """Class to create new dashboard theme"""
    _name = 'dashboard.theme'
    _description = 'Dashboard Theme'

    name = fields.Char(string='Theme Name', help='Name of the theme')
    color_x = fields.Char(string='Color X', help='Select the color_x for theme',
                          default='#4158D0')
    color_y = fields.Char(string='Color Y', help='Select the color_y for theme',
                          default='#C850C0')
    color_z = fields.Char(string='Color Z', help='Select the color_z for theme',
                          default='#FFCC70')
    body = fields.Html(string='Body', compute='_compute_gradient', store=True,
                       readonly=True,
                       help='Preview of the theme will be shown')
    style = fields.Char(string='Style', compute='_compute_gradient',
                        store=True, readonly=True,
                        help='It store the style of the gradient')

    @api.depends('color_x', 'color_y', 'color_z')
    def _compute_gradient(self):
        """Build the gradient style of the theme, and its preview block."""
        for theme in self:
            style = (
                "background-image: linear-gradient(50deg, "
                f"{theme.color_x} 0%, {theme.color_y} 46%, "
                f"{theme.color_z} 100%);"
            )
            theme.style = style
            theme.body = (
                f"<div style='width:300px; height:300px;{style}'/>"
            )

    def get_records(self):
        """
            Function for returning all records with fields name and style
        """
        records = self.search_read([], ['name', 'style'])
        return records
