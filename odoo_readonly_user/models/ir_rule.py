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
from odoo.fields import Domain


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
            return Domain.AND([res, Domain.FALSE])
        return res
