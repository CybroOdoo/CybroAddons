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
from odoo import api, fields, models


class FleetVehicleInherit(models.Model):
    """ inherit model and add inspection lines"""
    _inherit = 'fleet.vehicle'

    inspection_line_ids = fields.One2many('inspection.request.line',
                                          'fleet_vehicle_id',
                                          string='Inspection Line',
                                          help='Vehicle Inspection Lines')
    is_inspection_active = fields.Boolean(string='Inspection active',
                                          help='Active Vehicle Inspection',
                                          default=False)
    inspection_count = fields.Integer(string='Inspections',
                                      help='Number of inspections',
                                      compute='_compute_inspection_count')

    def get_inspection_requests(self):
        """Inspection smart button"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vehicle Inspections',
            'view_mode': 'tree,form',
            'res_model': 'inspection.request',
            'domain': [('vehicle_id', '=', self.id)],
        }

    @api.depends('is_inspection_active')
    def _compute_inspection_count(self):
        """ calculating the vehicle inspection number """
        self.inspection_count = self.env['inspection.request'].search_count(
            [('vehicle_id', '=', self.id)])


class FleetVehicleLogServicesInherit(models.Model):
    """inherit fleet service add sub service types"""
    _inherit = 'fleet.vehicle.log.services'

    fleet_service_id = fields.Many2one(
        'fleet.vehicle.log.services',
        help='Fleet service', string='Fleet service')
    sub_service_ids = fields.One2many('fleet.service.inspection',
                                      'service_id',
                                      help='Sub Service Lines',
                                      string='Sub Service Lines')
    inspection_reference = fields.Integer(string='Inspection Reference',
                                          help='Inspection Reference')
    inspection_name = fields.Char(string='Inspection',
                                  help='Vehicle Inspection name')


class FleetSubServiceTypes(models.Model):
    """model for create service wizard"""
    _name = 'fleet.sub.service.type'
    _description = 'Fleet Sub Service Type'

    service_type_id = fields.Many2one('fleet.service.type',
                                      help='Vehicle service type',
                                      string='Vehicle service type')
    service_category = fields.Char(string='Category',
                                   help='Vehicle service category',)

    @api.onchange('service_type_id')
    def _onchange_service_type_id(self):
        """select service category """
        for rec in self:
            rec.service_category = rec.service_type_id.category
