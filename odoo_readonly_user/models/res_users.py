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
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    """Inherits ResUsers model for supering the write function"""
    _inherit = 'res.users'

    is_readonly = fields.Boolean("Readonly", default=False)

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
