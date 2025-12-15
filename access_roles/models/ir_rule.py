# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval


class IrRule(models.Model):
    """Extend ir.rule to apply role-based UI restrictions."""
    _inherit = "ir.rule"

    def _compute_domain(self, model_name, mode="read"):
        """
        Override _compute_domain to include role-based domain restrictions.
        """
        # Skip custom logic for 'res.users' to prevent recursion during user model loading
        if model_name == 'res.users' or self.env.context.get("skip_role_domain"):
            return super()._compute_domain(model_name, mode=mode)

        # Use sudo() to bypass rules when accessing user fields (breaks recursion)
        env = self.env(context=dict(self.env.context, skip_role_domain=True))
        user = env.user.sudo()

        access_role = user.access_role_id
        user_roles = user.access_role_id.role_management_id
        role_domains = []
        for role in user_roles:
            for access in role.domain_ids:
                if access.domain_model_name == model_name and access.name:
                    role_domains.append(safe_eval(access.name))

        base_domain = super()._compute_domain(model_name, mode=mode)
        # Normalize base_domain to a list (Odoo's default if no rules: False/None -> [])
        base_domain = base_domain or []

        if role_domains:
            role_domain_combined = expression.OR(role_domains)
            return expression.AND([base_domain, role_domain_combined])
        return base_domain
