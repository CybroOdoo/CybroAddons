# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: AYANA KP (odoo@cybrosys.com)
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
################################################################################
from odoo import api, models


class IrModelAccess(models.Model):
    """Inherits the ir model access for restricting
     the user from accessing data."""
    _inherit = 'ir.model.access'

    @api.model
    def check(self, model_name, mode='read', raise_exception=True):
        """Overrides the default check method to allow
         only read access to the user."""
        model = ['res.users.log', 'mail.channel', 'mail.alias',
                 'bus.presence', 'res.lang',
                 'mail.channel.member']
        user_id = self.env.uid
        query = """
                        SELECT
                            res_groups.name
                        FROM
                            res_users
                        JOIN
                            res_groups_users_rel ON res_users.id = res_groups_users_rel.uid
                        JOIN
                            res_groups ON res_groups.id = res_groups_users_rel.gid
                        JOIN
                            ir_model_data ON res_groups.id = ir_model_data.res_id
                        WHERE
                            res_users.id = %s
                            AND ir_model_data.module = 'odoo_readonly_user'
                            AND ir_model_data.name = 'group_users_readonly';
                    """
        self.env.cr.execute(query, (user_id,))
        groups = self.env.cr.fetchall()
        res = super().check(model_name, mode='read', raise_exception=raise_exception)
        if groups and model_name not in model and mode in (
                'write', 'create', 'unlink'):
            return False
        return res
