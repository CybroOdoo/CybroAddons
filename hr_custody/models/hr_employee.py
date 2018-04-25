# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Authors: Avinash Nk, Jesni Banu (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import models, fields, api, _


class HrCustody(models.Model):
    _inherit = 'hr.employee'

    custody_count = fields.Integer(compute='_custody_count', string='# Custody')
    equipment_count = fields.Integer(compute='_equipment_count', string='# Equipments')

    # count of all custody contracts
    @api.multi
    def _custody_count(self):
        for each in self:
            custody_ids = self.env['hr.custody'].search([('employee', '=', each.id)])
            each.custody_count = len(custody_ids)

    # count of all custody contracts that are in approved state
    @api.multi
    def _equipment_count(self):
        for each in self:
            equipment_obj = self.env['hr.custody'].search([('employee', '=', each.id), ('state', '=', 'approved')])
            equipment_ids = []
            for each1 in equipment_obj:
                if each1.custody_name.id not in equipment_ids:
                    equipment_ids.append(each1.custody_name.id)
            each.equipment_count = len(equipment_ids)

    # smart button action for returning the view of all custody contracts related to the current employee
    @api.multi
    def custody_view(self):
        for each1 in self:
            custody_obj = self.env['hr.custody'].search([('employee', '=', each1.id)])
            custody_ids = []
            for each in custody_obj:
                custody_ids.append(each.id)
            view_id = self.env.ref('hr_custody.hr_custody_form_view').id
            if custody_ids:
                if len(custody_ids) <= 1:
                    value = {
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'hr.custody',
                        'view_id': view_id,
                        'type': 'ir.actions.act_window',
                        'name': _('Custody'),
                        'res_id': custody_ids and custody_ids[0]
                    }
                else:
                    value = {
                        'domain': str([('id', 'in', custody_ids)]),
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'hr.custody',
                        'view_id': False,
                        'type': 'ir.actions.act_window',
                        'name': _('Custody'),
                        'res_id': custody_ids
                    }

                return value

    # smart button action for returning the view of all custody contracts that are in approved state,
    # related to the current employee
    @api.multi
    def equipment_view(self):
        for each1 in self:
            equipment_obj = self.env['hr.custody'].search([('employee', '=', each1.id), ('state', '=', 'approved')])
            equipment_ids = []
            for each in equipment_obj:
                if each.custody_name.id not in equipment_ids:
                    equipment_ids.append(each.custody_name.id)
            view_id = self.env.ref('hr_custody.custody_custody_form_view').id
            if equipment_ids:
                if len(equipment_ids) <= 1:
                    value = {
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'custody.property',
                        'view_id': view_id,
                        'type': 'ir.actions.act_window',
                        'name': _('Equipments'),
                        'res_id': equipment_ids and equipment_ids[0]
                    }
                else:
                    value = {
                        'domain': str([('id', 'in', equipment_ids)]),
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'custody.property',
                        'view_id': False,
                        'type': 'ir.actions.act_window',
                        'name': _('Equipments'),
                        'res_id': equipment_ids
                    }

                return value
