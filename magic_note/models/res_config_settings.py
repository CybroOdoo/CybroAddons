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


class ResConfigSettings(models.TransientModel):
    """ Inherits the class to set the color to be applied for notes when the
    current date is before, after deadline, or if the deadline date is not
    within the interval. """
    _inherit = 'res.config.settings'

    note_color_default = fields.Selection(
        [('white', 'White'), ('grey', 'Grey'), ('orange', 'Orange'),
         ('green', 'Green'), ('blue', 'Blue'), ('purple', 'Purple'),
         ('pink', 'Pink'), ('red', 'Red')], string='Default Color',
        config_parameter='magic_note.note_color_default',
        help='This color will be set to the records if no date interval '
             'record is found.')
    not_in_interval = fields.Selection(
        [('white', 'White'), ('grey', 'Grey'), ('orange', 'Orange'),
         ('green', 'Green'), ('blue', 'Blue'), ('purple', 'Purple'),
         ('pink', 'Pink'), ('red', 'Red')],
        string='If Not Inside The Interval',
        config_parameter='magic_note.not_in_interval',
        help='This color will be set to notes if none of the deadline date '
             'come under any defined interval stages.')
    after_deadline = fields.Selection(
        [('white', 'White'), ('grey', 'Grey'), ('orange', 'Orange'),
         ('green', 'Green'), ('blue', 'Blue'), ('purple', 'Purple'),
         ('pink', 'Pink'), ('red', 'Red')], string='After Deadline',
        config_parameter='magic_note.after_deadline',
        help='This color will be set to the notes once they cross the '
             'deadline date.')
