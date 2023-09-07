# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Rahul CK(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import fields, models


class NoteColor(models.Model):
    """Specify the colors and intervals that is to be applied to the notes"""
    _name = 'note.color'
    _description = 'Note Colour Interval Fields'

    name = fields.Char(string="Criteria", help="Name for this date interval")
    color_note = fields.Selection(
        [('white', 'White'), ('grey', 'Grey'), ('orange', 'Orange'),
         ('green', 'Green'), ('blue', 'Blue'), ('purple', 'Purple'),
         ('pink', 'Pink'), ('red', 'Red')], required=True, default='white',
        help="Colour of the record")
    start_interval = fields.Integer(string="Lower limit", default='1',
                                    required=True,
                                    help="Starting interval should be a "
                                         "integer (Number of days)")
    end_interval = fields.Integer(string="Upper limit", default='2',
                                  required=True,
                                  help="End interval  should be a integer "
                                       "(Number of days)")
