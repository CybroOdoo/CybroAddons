# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models


class FleetReserved(models.Model):
    """
    Model for recording reserved time for fleet vehicles.

    This class defines the model for tracking reserved time for fleet vehicles.
    """

    _name = "fleet.reserved"
    _description = "Fleet reserved"

    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  help="Employee who have vehicle reserved")
    date_from = fields.Datetime(string='Reserved Date From',
                                help='Reserved Date From')
    date_to = fields.Datetime(string='Reserved Date To',
                              help='Reserved Date To')
    reserved_obj_id = fields.Many2one('fleet.vehicle',
                                      string='Reserved Vehicle',
                                      help='Reserved Vehicle')
