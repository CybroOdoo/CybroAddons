# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nilmar Shereef(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api, exceptions, _


class SelectColor(models.Model):
    _name = "set.progressbar.color"
    _rec_name = 'color'

    range_start = fields.Integer(string='Range From(%)', required=True, help="Starting range of Statusbar in Percentage")
    range_stop = fields.Integer(string='Range To(%)', required=True, help="Stop range of Statusbar in Percentage")
    color = fields.Selection([('red', 'Red'), ('green', 'Green'), ('yellow', 'Yellow'),
                             ('pink', 'Pink'), ('orange', 'Orange'),
                             ('light_green', 'Light Green'), ('grey', 'Grey'),
                              ('blue', 'Blue'), ('purple', 'Purple'),
                              ('black', 'Black'), ('brown', 'Brown')],
                             string='Color', required=True, default='red',
                             help="Choose a color for selected range")

    @api.multi
    def assign_progress_bar_color(self):
        values = self.env['set.progressbar.color'].search([])
        list_ret = []
        for value in values:
            list_temp = []
            list_temp.append(value.range_start)
            list_temp.append(value.range_stop)
            list_temp.append(value.color)
            list_ret.append(list_temp)
        return list_ret

    @api.multi
    @api.constrains('range_start', 'range_stop')
    def check_range(self):
        if self.range_start > self.range_stop:
            raise exceptions.ValidationError("Start range should be less than stop range")
