# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models


class HrDepartment(models.Model):
    """Inherit hr.department to add hierarchical organization chart features."""
    _inherit = 'hr.department'

    child_org_ids = fields.One2many(
        'hr.department',
        'master_department_id',
        string='Child Departments',
        help='Department lines for organizational hierarchy.'
    )
    is_parent_child = fields.Boolean(
        string='Is Parent or Child',
        help='Indicates whether the department has a parent or child department.'
    )

    @api.model
    def get_child_dept(self, department_id):
        """Fetch hierarchy data for the widget."""
        department = self.browse(department_id)
        parent = department.parent_id
        child_data = [{'name': child.name, 'id': child.id} for child in
                      department.child_ids]
        return {
            'parent': {
                'name': parent.name,
                'id': parent.id
            } if parent else None,
            'self': department.name,
            'child': child_data
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Set hierarchy flag upon department creation."""
        res = super().create(vals_list)
        for record in res:
            record.is_parent_child = bool(record.parent_id or record.child_ids)
        return res

    def write(self, values):
        """Update hierarchy flag upon department modification."""
        res = super().write(values)
        if 'parent_id' in values or 'child_ids' in values:
            for record in self:
                record.is_parent_child = bool(record.parent_id or record.child_ids)
        return res
