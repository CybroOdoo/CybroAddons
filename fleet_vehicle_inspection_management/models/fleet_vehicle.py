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
from odoo import api, fields, models

"""model to inherit vehicles in fleet"""


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

    fleet_service_id = fields.Many2one('fleet.vehicle.log.services',
                                       help='Fleet service',
                                       string='Fleet service')
    sub_service_ids = fields.One2many('fleet.service.inspection',
                                      'service_id', help='Sub Service Lines',
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
