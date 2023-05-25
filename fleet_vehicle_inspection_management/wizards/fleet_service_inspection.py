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
""" create service from inspection requests"""
from odoo import api, fields, models


class FleetServiceInspection(models.TransientModel):
    """ create vehicle service"""
    _name = 'fleet.service.inspection'

    service_subtype_ids = fields.Many2many('fleet.service.type',
                                           string='Sub service Type',
                                           help='Related filed for the '
                                                'sub service type')
    inspection_reference = fields.Integer(string='Inspection_id',
                                          help='Inspection Id')
    service_type_id = fields.Many2one('fleet.service.type', string='Services',
                                      help='Services')
    service_id = fields.Many2one('fleet.vehicle.log.services',
                                 help='Service Reference',
                                 string='Service Reference')
    service_log_id = fields.Many2one('vehicle.service.log',
                                     help='Service log Reference',
                                     string='Service log Reference')
    service_category = fields.Selection([('service', 'Service'),
                                         ('contract', 'Contract'), ],
                                        help='Service Category type.',
                                        string='Service Category')
    vehicle_id = fields.Many2one('fleet.vehicle', help='Vehicle',
                                 string='Vehicle')
    odometer = fields.Float(string='Last Odometer',
                            help='Odometer measure of the vehicle at the moment of this log')
    odometer_unit = fields.Selection([('kilometers', 'km'),
                                       ('miles', 'mi')
                                       ], 'Odometer Unit',
                                     default='kilometers', required=True)
    sub_service_reference = fields.Integer(string='Sub Services',
                                           help='Vehicle sub service ')
    log_sub_service = fields.Integer(string='Sub Services',
                                     help='Vehicle sub service ')
    amount = fields.Monetary(string='Cost', help='Amount',)
    date = fields.Date(string='Vehicle Service Date',
                       help='Vehicle Service Date',
                       String='Vehicle Service Date')
    company_id = fields.Many2one('res.company', string='Company',
                                 help='Company',
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency', help='Currency')
    vendor_id = fields.Many2one('res.partner', string='Vendor', help='Vendor')

    @api.onchange('service_type_id')
    def _onchange_service_category(self):
        """ function to service category """
        self.vehicle_id = self.service_log_id.vehicle_id.id
        for rec in self:
            rec.service_category = rec.service_type_id.category

    def action_create_service(self):
        """ create vehicle service"""
        service_id = self.env['fleet.vehicle.log.services'].search([
            ('inspection_reference', '=', self.id)])
        if not service_id:
            inspection_id = self.env['inspection.request'].browse(
                self.inspection_reference)
            self.env['fleet.vehicle.log.services'].create({
                'inspection_reference': self.id,
                'description': inspection_id.inspection_id.name,
                'service_type_id': self.service_type_id.id,
                'date': fields.Date.today(),
                'vehicle_id': self.vehicle_id.id,
                'odometer': self.odometer,
                'sub_service_ids': [(0, 0, {
                    'service_type_id': rec.id,
                    'vehicle_id': self.vehicle_id.id,
                    'sub_service_reference': rec.id,
                    'service_category': rec.category,
                }) for rec in self.service_subtype_ids]
            })[0]
        else:
            for rec in self.service_subtype_ids:
                sub_service_id = self.env['fleet.service.inspection'].search([
                    ('sub_service_reference', '=', rec.id)])
                if not sub_service_id:
                    service_id.write({
                        'sub_service_ids': [(0, 0, {
                            'service_type_id': rec.id,
                            'vehicle_id': self.vehicle_id.id,
                            'sub_service_reference': rec.id,
                            'service_category': rec.category,
                        })],
                    })
        service_log_id = self.env['vehicle.service.log'].search([
            ('service_reference', '=', self.id)])
        if not service_log_id:
            inspection_id = self.env['inspection.request'].browse(
                self.inspection_reference)
            self.env['vehicle.service.log'].create({
                'service_reference': self.id,
                'vehicle_id': self.vehicle_id.id,
                'service_type_id': self.service_type_id.id,
                'amount': self.amount,
                'odometer': self.odometer,
                'odometer_unit': self.odometer_unit,
                'date': self.date,
                'vendor_id': self.vendor_id,
                'inspection_name': inspection_id.name,
                'inspection_result': inspection_id.inspection_result,
                'notes': inspection_id.internal_note,
                'additional_service_ids': [(0, 0, {
                    'service_type_id': rec.id,
                    'vehicle_id': self.vehicle_id.id,
                    'log_sub_service': rec.id,
                    'service_category': rec.category,
                }) for rec in self.service_subtype_ids],
                'service_image_ids': [(0, 0, {
                    'name': rec.name,
                    'image': rec.image,
                }) for rec in inspection_id.inspection_image_ids]
            })
        else:
            for rec in self.service_subtype_ids:
                sub_service_id = self.env['fleet.service.inspection'].search([
                    ('log_sub_service', '=', rec.id)])
                if not sub_service_id:
                    service_log_id.write({
                        'additional_service_ids': [(0, 0, {
                            'service_type_id': rec.id,
                            'vehicle_id': self.vehicle_id.id,
                            'service_log_id': rec.id,
                            'service_category': rec.category,
                        })],
                    })
