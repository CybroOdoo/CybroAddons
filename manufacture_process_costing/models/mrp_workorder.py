# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import models


class MrpWorkorder(models.Model):
    """This class inherits the existing class with model name mrp.workorder
    to define a function to automatically calculate the costings"""
    _inherit = 'mrp.workorder'

    def button_finish(self):
        """Super the button_finish button in workorder and update the
        actual_minute and actual_quantity of labour_cost_ids,
        overhead_cost_ids, material_cost_ids according to the settings value"""
        res = super(MrpWorkorder, self).button_finish()
        process = self.env['ir.config_parameter'].sudo()
        process_value = process.get_param(
            'manufacture_process_costing.process_costing_method')
        if process_value == 'work-center':
            for rec in self.production_id.labour_cost_ids:
                for val in self:
                    if rec.operation == val.name:
                        labour_id = rec.id
                        self.production_id.write({
                            'labour_cost_ids': [
                                (1, labour_id, {
                                    'actual_minute': rec.duration
                                }) for rec in self]
                        })
            for rec in self.production_id.overhead_cost_ids:
                for val in self:
                    if rec.operation == val.name:
                        overhead_id = rec.id
                        self.production_id.write({
                            'overhead_cost_ids': [
                                (1, overhead_id, {
                                    'actual_minute': rec.duration
                                }) for rec in self]
                        })
            self.production_id.write({
                'material_cost_ids': [
                    (1, rec.id, {
                        'actual_quantity': rec.planned_qty
                    }) for rec in self.production_id.material_cost_ids]
                })
        return res
