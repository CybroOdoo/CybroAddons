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


class NoteConfiguration(models.Model):
    """Specify the colours for notes based on deadline"""
    _name = 'note.config'
    _rec_name = "default_magic_color"
    _description = 'Note Colour Settings Field'

    default_magic_color = fields.Selection(
        [('white', 'White'), ('grey', 'Grey'), ('orange', 'Orange'),
         ('green', 'Green'), ('blue', 'Blue'), ('purple', 'Purple'),
         ('pink', 'Pink'), ('red', 'Red')], string="Default", required=True,
        default='white', help="This color will be set to the records if no "
                              "date interval record is found By default "
                              "records are coloured to white")
    not_in_interval = fields.Selection(
        [('white', 'White'), ('grey', 'Grey'), ('orange', 'Orange'),
         ('green', 'Green'), ('blue', 'Blue'), ('purple', 'Purple'),
         ('pink', 'Pink'), ('red', 'Red')],
        string="If Not inside the Interval", required=True, default='grey',
        help="This color will be set to the records which doesn't come under "
             "any defined interval stages. By default the records are coloured"
             " to Grey")
    deadline_cross = fields.Selection(
        [('white', 'White'), ('grey', 'Grey'), ('orange', 'Orange'),
         ('green', 'Green'), ('blue', 'Blue'), ('purple', 'Purple'),
         ('pink', 'Pink'), ('red', 'Red')], string="After deadline ",
        required=True, default='blue',
        help="This color will be set to the notes once they cross the dead "
             "date")
