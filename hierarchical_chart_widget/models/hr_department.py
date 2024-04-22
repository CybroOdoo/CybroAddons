# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class HrDepartment(models.Model):
    """This model is used for storing a field in contacts"""
    _inherit = 'hr.department'

    child_org_ids = fields.One2many('hr.department',
                                    'master_department_id',
                                    help='Department Lines')
    is_parent_child = fields.Boolean(string='Is parent ')

    @api.model
    def get_child_dept(self, department_id, model):
        """Fetching the datas to widget"""
        model_id = self.env['ir.model'].search([('model', '=', model)])
        department_id = self.env[model_id.model].browse(department_id)
        parent_id = department_id.parent_id
        child_data = [{'name': child.name, 'id': child.id} for child in
                      department_id.child_ids]

        result = {
            'parent': {
                'name': parent_id.name,
                'id': parent_id.id
            } if parent_id else None,
            'self': department_id.name,
            'child': child_data
        }
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """To show the widget at the time of creation"""
        res = super(HrDepartment, self).create(vals_list)
        for record in res:
            if record.parent_id or record.child_ids:
                record.is_parent_child = True
            else:
                record.is_parent_child = False
        return res

    def write(self, values):
        """To update the widget at the time of update"""
        res = super(HrDepartment, self).write(values)
        if 'parent_id' in values:
            self.is_parent_child = True
        return res
