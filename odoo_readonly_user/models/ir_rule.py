# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
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
from odoo import api, models, _
from odoo.osv import expression
from odoo.exceptions import ValidationError


class IrRule(models.Model):
    """Inherits the ir rule for restricting the user from accessing data."""
    _inherit = 'ir.rule'

    @api.model
    def _compute_domain(self, model_name, mode):
        res = super()._compute_domain(model_name, mode)
        readonly_models = ['res.users.log', 'res.users', 'mail.channel',
                           'mail.alias', 'bus.presence', 'res.lang',
                           'mail.channel.member']
        if self.env.user.has_group(
                'odoo_readonly_user.group_users_readonly') \
                and model_name not in readonly_models \
                and mode in ('write', 'create', 'unlink'):
            return expression.AND([res, expression.FALSE_DOMAIN])
        return res


class ResUsers(models.Model):
    """Inherits ResUsers model for supering the write function"""
    _inherit = 'res.users'

    def write(self, vals):
        """Super the write function for adding validation based on
         the conditions"""
        group_obj = self.env['res.groups'].sudo().browse(
            self.env.ref('odoo_readonly_user.group_users_readonly').id)
        if str(group_obj.id) in str(vals):
            if self.id == self.env.user.id:
                raise ValidationError(
                    _("Readonly access denied for Admin"))
            else:
                super(ResUsers, self).write(vals)
        else:
            super(ResUsers, self).write(vals)
