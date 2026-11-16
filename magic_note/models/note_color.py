# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NoteColor(models.Model):
    """ Specify the colors and date intervals that is to be applied to the notes """
    _name = 'note.color'
    _description = 'Note Color Intervals'

    name = fields.Char(
        string='Criteria',
        help='Title for date interval'
    )

    color_note = fields.Selection(
        [('white', 'White'),
         ('grey', 'Grey'),
         ('orange', 'Orange'),
         ('green', 'Green'),
         ('blue', 'Blue'),
         ('purple', 'Purple'),
         ('pink', 'Pink'),
         ('red', 'Red')],
        string='Note Color',
        default='white',
        help='Color of the record'
    )

    start_interval = fields.Date(
        string='Start Date',
        help='Start date for color interval'
    )

    end_interval = fields.Date(
        string='End Date',
        help='End date for color interval'
    )

    @api.constrains('start_interval', 'end_interval')
    def _check_interval_dates(self):
        """
        Validation for date intervals
        """

        for record in self:

            if (
                record.start_interval
                and record.end_interval
                and record.start_interval > record.end_interval
            ):
                raise ValidationError(
                    self.env._("Lower Limit should not be greater than Upper Limit.")
                )
