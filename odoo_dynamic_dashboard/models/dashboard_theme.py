# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class DashboardTheme(models.Model):
    _name = 'dashboard.theme'
    _description = 'Dashboard Theme'

    name = fields.Char(string='Theme Name', help='Name of the theme')
    color_x = fields.Char(string='Color X', help='Select the color_x for theme',
                          default='#4158D0')
    color_y = fields.Char(string='Color Y', help='Select the color_y for theme',
                          default='#C850C0')
    color_z = fields.Char(string='Color Z', help='Select the color_z for theme',
                          default='#FFCC70')
    body = fields.Html(string='Body', help='Preview of the theme will be shown')
    style = fields.Char(string='Style',
                        help='It store the style of the gradient')

    @api.constrains('name', 'color_x', 'color_y', 'color_z')
    def save_record(self):
        """
            Function for saving the datas including body and style
        """
        self.body = f"<div style='width:300px; height:300px;background-image: linear-gradient(50deg, {self.color_x} 0%, {self.color_y} 46%, {self.color_z} 100%);'/>"
        self.style = f"background-image: linear-gradient(50deg, {self.color_x} 0%, {self.color_y} 46%, {self.color_z} 100%);"

    def get_records(self):
        """
            Function for returning all records with fields name and style
        """
        records = self.search_read([], ['name', 'style'])
        return records
