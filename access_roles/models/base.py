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
import logging
from odoo import api, models
from odoo.fields import Domain
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class Base(models.AbstractModel):
    """Extend base to apply role-based domain restrictions.
    In Odoo 20, ir.rule was removed and merged into ir.access and BaseModel._access_domain.
    """
    _inherit = 'base'

    @api.model
    def _access_domain(self, operation: str) -> Domain:
        """
        Override _access_domain to include role-based domain restrictions.
        """
        base_domain = super()._access_domain(operation)
        if self.env.su:
            return base_domain
        user = self.env.user.sudo()
        role = user.access_role_id
        if not role:
            return base_domain
        user_roles = self.env['role.management'].sudo().search([('role_ids', 'in', role.id)])
        if role.role_management_id:
            user_roles |= role.role_management_id
        if not user_roles:
            return base_domain
        role_domains = []
        eval_context = None
        for role in user_roles:
            for access in role.domain_ids:
                if access.domain_model_name == self._name and access.name:
                    if eval_context is None:
                        eval_context = self.env['ir.access']._eval_context()
                    try:
                        domain_val = safe_eval(access.name, eval_context)
                        if domain_val:
                            role_domains.append(Domain(domain_val))
                    except Exception as err:
                        _logger.debug("Failed to evaluate domain expression for %s: %s", self._name, err)
        if role_domains:
            role_domain_combined = Domain.OR(role_domains)
            return base_domain & role_domain_combined
        return base_domain

