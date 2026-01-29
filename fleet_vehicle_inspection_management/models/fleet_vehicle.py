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


class FleetVehicleInherit(models.Model):
    """ Inherit model and add inspection lines"""
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
            'domain': [('vehicle_id', '=', self.id)]}

    @api.depends('is_inspection_active')
    def _compute_inspection_count(self):
        """ Calculating the vehicle inspection number """
        self.inspection_count = self.env['inspection.request'].search_count(
            [('vehicle_id', '=', self.id)])
