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
from odoo import api, models
from odoo.fields import Domain


class Base(models.AbstractModel):
    """Inherits base model for restricting write, create, and unlink
    operations for read-only users in Odoo 19.5."""
    _inherit = 'base'

    @api.model
    def _access_domain(self, operation):
        res = super()._access_domain(operation)
        readonly_models = [
            'res.users.log', 'res.users', 'mail.channel', 'discuss.channel',
            'mail.alias', 'bus.presence', 'res.lang',
            'mail.channel.member', 'discuss.channel.member',
            'res.groups', 'ir.access', 'ir.model', 'ir.model.fields', 'ir.model.data',
        ]
        if (
            self.env.user.has_group('odoo_readonly_user.group_users_readonly')
            and self._name not in readonly_models
            and operation in ('write', 'create', 'unlink')
        ):
            return Domain.AND([res, Domain.FALSE])
        return res
