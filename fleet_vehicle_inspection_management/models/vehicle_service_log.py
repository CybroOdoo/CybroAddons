# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
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
""" vehicle inspection and service details"""
from odoo import fields, models


class VehicleServiceLog(models.Model):
    """ add vehicle inspection details"""
    _name = 'vehicle.service.log'
    _description = 'Vehicle Service Log'
    _inherit = 'fleet.vehicle.log.services'

    service_image_ids = fields.One2many('inspection.images', 'service_log_id',
                                        help='Inspection Images',
                                        string='Inspection Images')
    additional_service_ids = fields.One2many('fleet.service.inspection',
                                             'service_log_id',
                                             help='Additional Services',
                                             string='Additional Services')
    inspection_result = fields.Char(string='Inspection Result',
                                    help='Result of inspection')
    notes = fields.Html(string='Internal Notes', help='Internal notes')
    service_reference = fields.Integer(string='Service Reference',
                                       help='Service Reference')
