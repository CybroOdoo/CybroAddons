# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Harshitha AP (Contact : odoo@cybrosys.com)
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
    _inherit = 'pos.session'

    def get_pos_restriction_data(self):
        """
        Returns restriction fields for all employees and users.
        Also returns the list of employee IDs that have 'advanced rights'
        in any POS config — these employees bypass all restrictions.
        """
        advanced_employee_ids = set()
        pos_configs = self.env['pos.config'].sudo().search([])
        for config in pos_configs:
            if hasattr(config, 'advanced_employee_ids'):
                for emp in config.advanced_employee_ids:
                    advanced_employee_ids.add(str(emp.id))

        employees = self.env['hr.employee'].sudo().search_read(
            [], ['id', 'name'] + POS_FIELDS
        )
        users = self.env['res.users'].sudo().search_read(
            [], ['id', 'name'] + POS_FIELDS
        )

        return {
            'employees': {str(e['id']): e for e in employees},
            'users': {str(u['id']): u for u in users},
            'advanced_ids': list(advanced_employee_ids),
        }