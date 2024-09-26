# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models


class MovieScreen(models.Model):
    """
        Model for managing movie screens with details like name, total rows,
        seats per row, and total seat count.
    """
    _name = 'movie.screen'
    _description = 'Movie Screen'

    name = fields.Char(string='Name of the screen',
                       help='Mention the name of the screen')
    total_rows = fields.Integer(string='Number of total Rows',
                                help='Mention the number of total rows.')
    no_of_seat_row = fields.Integer(string='Number of seat per row',
                                    help='Mention the number of seats per row')
    total_seat_count = fields.Integer(string='Total seats',
                                      compute='_compute_total_seat_count',
                                      help='Calculates the total seats')

    @api.constrains('total_rows', 'no_of_seat_row')
    def _compute_total_seat_count(self):
        """ Function for computing total seats in the screen."""
        for record in self:
            if record.total_rows and record.no_of_seat_row:
                record.total_seat_count = record.total_rows * record.no_of_seat_row
            else:
                record.total_seat_count = 0
