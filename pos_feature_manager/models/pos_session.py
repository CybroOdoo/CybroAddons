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

from odoo import models

POS_FIELDS = [
    'pos_allow_numpad',
    'pos_allow_payments',
    'pos_allow_discount',
    'pos_allow_qty',
    'pos_allow_price_edit',
    'pos_allow_remove_order_line',
    'pos_allow_customer_selection',
    'pos_allow_plus_minus',
]


class PosSession(models.Model):
    """Provide POS feature restrictions to active sessions."""
    _inherit = 'pos.session'

    def get_pos_restriction_data(self, *args, **kwargs):
        """
        Returns restriction fields for all employees and users.
        Also returns the list of employee IDs that have 'advanced rights'
        in any POS config — these employees bypass all restrictions.
        """
        advanced_employee_ids = set()
        pos_config_model = self.env['pos.config']
        role_fields = [f for f in ('manager_employee_ids', 'advanced_employee_ids') if f in pos_config_model._fields]
        if role_fields:
            if self and hasattr(self, 'config_id') and self.config_id:
                configs = self.config_id
            else:
                domain = [('active', '=', True)]
                if len(role_fields) == 1:
                    domain.append((role_fields[0], '!=', False))
                else:
                    domain.extend(['|', (role_fields[0], '!=', False), (role_fields[1], '!=', False)])
                configs = pos_config_model.sudo().search(domain)
            for config in configs:
                for field in role_fields:
                    for emp in getattr(config, field):
                        advanced_employee_ids.add(str(emp.id))

        employees = self.env['hr.employee'].sudo().search_read(
            [('active', '=', True)], ['id', 'user_id'] + POS_FIELDS
        )
        users = self.env['res.users'].sudo().search_read(
            [('active', '=', True)], ['id'] + POS_FIELDS
        )

        emp_dict = {}
        emp_to_user_map = {}
        for employee in employees:
            user_val = employee.get('user_id')
            if isinstance(user_val, (list, tuple)) and user_val:
                u_id = user_val[0]
            elif isinstance(user_val, int):
                u_id = user_val
            else:
                u_id = False
            emp_copy = dict(employee)
            emp_copy['user_id_int'] = u_id
            emp_dict[str(employee['id'])] = emp_copy
            if u_id:
                emp_to_user_map[str(employee['id'])] = str(u_id)

        return {
            'employees': emp_dict,
            'users': {str(user['id']): user for user in users},
            'emp_to_user_map': emp_to_user_map,
            'advanced_ids': list(advanced_employee_ids),
        }
