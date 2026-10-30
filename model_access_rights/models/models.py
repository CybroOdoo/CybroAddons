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
from odoo import api, models, _
from odoo.exceptions import UserError


class Base(models.AbstractModel):
    _inherit = 'base'

    def _check_access_restriction(self, operation_field):
        """Check if the current user or group is restricted from performing the given operation."""
        if self.env.is_admin() or self.env.su:
            return
        if self._abstract or self._transient:
            return
        if self._name in ('access.right', 'ir.model', 'ir.model.data', 'res.users', 'res.groups'):
            return

        current_model_id = self.env['ir.model'].sudo().search(
            [('model', '=', self._name)], limit=1).id

        if not current_model_id:
            return

        access_right_rec = self.env['access.right'].sudo().search_read(
            [('model_id', '=', current_model_id)],
            ['model_id', operation_field, 'restriction_type', 'user_id', 'groups_id']
        )

        if not access_right_rec:
            return

        for rec in access_right_rec:
            if rec['restriction_type'] == 'group' and rec.get('groups_id'):
                group_data = self.env['ir.model.data'].sudo().search([
                    ('model', '=', 'res.groups'),
                    ('res_id', '=', rec['groups_id'][0])
                ], limit=1)

                if group_data:
                    group = f"{group_data.module}.{group_data.name}"
                    if self.env.user.has_group(group) and rec.get(operation_field):
                        raise UserError(
                            _('You are restricted from performing this'
                              ' operation. Please contact the'
                              ' administrator.'))

            elif rec['restriction_type'] == 'user' and rec.get('user_id'):
                if self.env.user.id == rec['user_id'][0] and rec.get(operation_field):
                    raise UserError(
                        _('You are restricted from performing this'
                          ' operation. Please contact the'
                          ' administrator.'))

    @api.model_create_multi
    def create(self, vals_list):
        self._check_access_restriction('is_create_or_update')
        return super().create(vals_list)

    def write(self, vals):
        self._check_access_restriction('is_create_or_update')
        return super().write(vals)

    def unlink(self):
        if not self:
            return True
        self._check_access_restriction('is_delete')
        return super().unlink()
