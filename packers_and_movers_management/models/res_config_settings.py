# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherit the model res.config.settings to add distance amount"""
    _inherit = 'res.config.settings'

    distance_amount = fields.Float(
        string='Distance Amount/KM',
        config_parameter='packers_and_movers_management.distance_amount',
        help="Enter the distance amount/KM")
    is_extra = fields.Boolean(
        string='Apply Extra Amount',
        config_parameter='packers_and_movers_management.is_extra',
        default=False,
        help="Enable, if extra charge want to add")
    extra_amount = fields.Float(
        string='Extra Amount',
        config_parameter='packers_and_movers_management.extra_amount',
        help='Enter extra amount/KM')
    is_distance_limited = fields.Boolean(
        string='Limit Distance',
        config_parameter='packers_and_movers_management.is_distance_limited',
        default=False,
        help="Enable, if need to limit "
             "Distance")
    max_distance = fields.Float(
        string='Maximum Distance (KM)',
        config_parameter='packers_and_movers_management.max_distance',
        help='Enter the maximum distance limit in KM'
    )
