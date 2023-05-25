# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
#    Version 3 (AGPL v3)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
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
