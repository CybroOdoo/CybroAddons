# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP (odoo@cybrosys.com)
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
from odoo import fields, models


class MaintenanceRequest(models.Model):
    """Model for managing Maintenance
    Requests. This class extends the base 'maintenance.request'
    model to include the ability to create work orders.
    """
    _inherit = 'maintenance.request'

    material_request_id = fields.Many2one('material.request')
    is_material_request = fields.Boolean(string='Material Request',
                                         help="Flag indicating if it's a material request")
    is_create_work_order = fields.Boolean(string='Work Order',
                                          compute='_compute_create_order_request',
                                          help="Flag indicating if a work order "
                                               "needs to be created")
    is_material_work_order = fields.Boolean(string='Material Request Work Order',
                                            compute='_compute_create_order_request',
                                            help="Flag indicating if a work order "
                                                 "needs to be created")

    def _compute_create_order_request(self):
        """
        Compute method to determine if a work order needs to be
        created based on material request status.
        """
        stages = {
            'stage_1': self.env.ref('maintenance.stage_1').id,
            'stage_3': self.env.ref('maintenance.stage_3').id,
            'stage_0': self.env.ref('maintenance.stage_0').id,
        }

        for record in self:
            request = self.env['material.request'].search(
                [('maintenance_request_id', '=', record.id)], limit=1)
            record.is_create_work_order = request and request.is_product_received

            stage_id = record.stage_id.id
            record.is_material_work_order = stage_id == stages.get('stage_1')
            if stage_id in (stages.get('stage_3'), stages.get('stage_0')):
                record.is_create_work_order = False

    def action_main_create_work_order(self):
        """ Open a form view to create a new maintenance work order.
        This method creates a new maintenance work order with default
        values and opens a form view to fill in additional details.
        :return: A dictionary defining the action to perform.
        """
        self.is_create_work_order = True
        self.stage_id = self.env.ref('maintenance.stage_1').id
        return {
            'name': 'Work Order',
            'view_mode': 'form',
            'res_model': 'maintenance.work',
            'view_id': self.env.ref(
                'work_orders_in_maintenance.maintenance_work_order_wizard_view_form').id,
            'type': 'ir.actions.act_window',
            'context': {'default_maintenance_request_id': self.id,
                        'default_equipment_id': self.equipment_id.id,
                        },
            'target': 'new'
        }

    def action_create_material_request(self):
        """ Open a form view to create a new Material Request.
        This method creates a new Material Request with default
        values and opens a form view to fill in additional details.
        :return: A dictionary defining the action to perform.
        """
        self.is_material_request = True
        self.is_create_work_order = False
        return {
            'name': 'Material Request',
            'view_mode': 'form',
            'res_model': 'material.request',
            'view_id': self.env.ref(
                'work_orders_in_maintenance.material_request_wizard_view_form').id,
            'type': 'ir.actions.act_window',
            'context': {'default_maintenance_request_id': self.id,
                        'default_equipment_id': self.equipment_id.id,
                        },
            'target': 'new'
        }
