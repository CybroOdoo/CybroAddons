# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: JANISH BABU (<https://www.cybrosys.com>)
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
from odoo import fields, models


class RecurrencePeriod(models.Model):
    """This class is used to create new model recurrence period"""
    _name = "recurrence.period"
    _description = "Recurrence Period "

    name = fields.Char(string="Name",
                       help='The name of the recurrence period. Enter a '
                            'descriptive name for the period.')
    duration = fields.Float(string="Duration",
                            help='The duration associated with this record. '
                                 'Enter the duration value.')
    unit = fields.Selection([('hours', 'hours'),
                             ('days', 'Days'), ('weeks', 'Weeks'),
                             ('months', 'Months'), ('years', 'Years')],
                            string='Unit',
                            help='Select the unit of time associated with this '
                                 'record. Choose from the available options.')
