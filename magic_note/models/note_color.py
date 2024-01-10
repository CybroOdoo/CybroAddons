# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Busthana Shirin (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class NoteColor(models.Model):
    """ Specify the colors and intervals that is to be applied to the notes """
    _name = 'note.color'
    _description = 'Note Color Intervals'

    name = fields.Char(string='Criteria', help='Title for date interval')
    color_note = fields.Selection(
        [('white', 'White'), ('grey', 'Grey'), ('orange', 'Orange'),
         ('green', 'Green'), ('blue', 'Blue'), ('purple', 'Purple'),
         ('pink', 'Pink'), ('red', 'Red')], string='Note Color',
        default='white', help='Color of the record')
    start_interval = fields.Integer(string='Lower Limit', default='1',
                                    help='Number of days to the deadline date')
    end_interval = fields.Integer(
        string='Upper Limit', default='2',
        help='Number of days after the deadline date')
