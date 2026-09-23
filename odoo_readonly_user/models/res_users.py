# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
        group_ref = self.env.ref('odoo_readonly_user.group_users_readonly', raise_if_not_found=False)
        if group_ref and str(group_ref.id) in str(vals):
            if any(user.id == self.env.user.id for user in self):
                raise ValidationError(
                    _("Readonly access denied for Admin"))
        return super(ResUsers, self).write(vals)
