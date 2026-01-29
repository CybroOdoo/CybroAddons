# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohamed Muzammil VP(odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class FleetServiceInspection(models.TransientModel):
    """ Create a vehicle service model"""
    _name = 'fleet.service.inspection'
    _description = 'Fleet Service'

    service_subtype_ids = fields.Many2many(
        'fleet.service.type', string='Sub service Type',
        help='Related filed for the sub service type')
    inspection_reference_id = fields.Many2one(
        'inspection.request', string='Inspection ID', help='Inspection Id')
    service_type_id = fields.Many2one(
        'fleet.service.type', string='Services', help='Services')
    service_id = fields.Many2one('fleet.vehicle.log.services',
                                 help='Service Reference',
                                 string='Service Reference')
    service_log_id = fields.Many2one('vehicle.service.log',
                                     help='Service log Reference',
                                     string='Service log Reference')
    service_category = fields.Selection(
        selection=[('service', 'Service'), ('contract', 'Contract'), ],
        help='Service Category type.', string='Service Category')
    vehicle_id = fields.Many2one('fleet.vehicle', help='Vehicle',
                                 string='Vehicle')
    odometer = fields.Float(string='Last Odometer',
                            help='Odometer measure of the vehicle at the '
                                 'moment of this log')
    odometer_unit = fields.Selection(
        selection=[('kilometers', 'km'), ('miles', 'mi')],
        string='Odometer Unit', default='kilometers', required=True,
        help='Odometer reading')
    sub_service_reference_id = fields.Many2one(
        'fleet.service.inspection', string='Sub Services',
        help='Vehicle sub service')
    log_sub_service_id = fields.Many2one('fleet.service.inspection',
                                         string='Sub Services',
                                         help='Vehicle sub service')
    amount = fields.Monetary(string='Cost', help='Amount',)
    date = fields.Date(string='Vehicle Service Date',
                       help='Vehicle Service Date',)
    company_id = fields.Many2one('res.company', string='Company',
                                 help='Company',
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency', help='Currency')
    vendor_id = fields.Many2one('res.partner', string='Vendor', help='Vendor')

    @api.onchange('service_type_id')
    def _onchange_service_category(self):
        """Function to service category """
        for rec in self:
            rec.service_category = rec.service_type_id.category

    def action_create_service(self):
        """Create vehicle service"""
        if not self.service_id:
            self.env['fleet.vehicle.log.services'].create({
                'inspection_reference_id': self.id,
                'description': self.inspection_reference_id.inspection_id.name,
                'service_type_id': self.service_type_id.id,
                'date': fields.Date.today(),
                'vehicle_id': self.vehicle_id.id,
                'odometer': self.odometer,
                'sub_service_ids': [(0, 0, {
                    'service_type_id': rec.id,
                    'vehicle_id': self.vehicle_id.id,
                    'sub_service_reference_id': rec.id,
                    'service_category': rec.category,
                }) for rec in self.service_subtype_ids]
            })[0]
        else:
            for rec in self.service_subtype_ids:
                if not self.sub_service_reference_id:
                    self.service_id.write({
                        'sub_service_ids': [(0, 0, {
                            'service_type_id': rec.id,
                            'vehicle_id': self.vehicle_id.id,
                            'sub_service_reference_id': rec.id,
                            'service_category': rec.category,
                        })],
                    })
        if not self.service_log_id:
            self.env['vehicle.service.log'].create({
                'service_reference_id': self.id,
                'vehicle_id': self.vehicle_id.id,
                'service_type_id': self.service_type_id.id,
                'amount': self.amount,
                'odometer': self.odometer,
                'odometer_unit': self.odometer_unit,
                'date': self.date,
                'vendor_id': self.vendor_id,
                'inspection_name': self.inspection_reference_id.name,
                'inspection_result': self.inspection_reference_id.inspection_result,
                'notes': self.inspection_reference_id.internal_note,
                'additional_service_ids': [(0, 0, {
                    'service_type_id': rec.id,
                    'vehicle_id': self.vehicle_id.id,
                    'log_sub_service_id': rec.id,
                    'service_category': rec.category,
                }) for rec in self.service_subtype_ids],
                'service_image_ids': [(0, 0, {
                    'name': rec.name,
                    'image': rec.image,
                }) for rec in self.inspection_reference_id.inspection_image_ids
                                      ]})
        else:
            for rec in self.service_subtype_ids:
                if not self.log_sub_service_id:
                    self.service_log_id.write({
                        'additional_service_ids': [(0, 0, {
                            'service_type_id': rec.id,
                            'vehicle_id': self.vehicle_id.id,
                            'service_log_id': rec.id,
                            'service_category': rec.category,
                        })],
                    })
