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
"""Franchise customer portal controller"""
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class FranchiseCustomerPortal(CustomerPortal):
    """Franchise Customer portal."""

    def _get_env(self):
        """Helper to get current environment safely."""
        try:
            return request.env
        except RuntimeError:
            return getattr(self, '_custom_env', None)

    def _prepare_portal_counter_values(self, counter):
        """Prepare portal counter values for Odoo 20."""
        if counter == 'franchise_count':
            env = self._get_env()
            domain = [('state', 'in', ('e_contract', 'f_signed', 'g_declined'))]
            if env and not env.user.has_group('base.group_system'):
                domain.append(('dealer_portal_user', '=', env.user.id))
            return 'franchise.dealer', domain, 'sudo'
        return super()._prepare_portal_counter_values(counter)

    def _prepare_home_portal_values(self, counters):
        """Preparing franchise count to view in portal."""
        values = {}
        if hasattr(super(), '_prepare_home_portal_values'):
            values = super()._prepare_home_portal_values(counters)
        if 'franchise_count' in counters:
            env = self._get_env()
            if env:
                domain = [('state', 'in', ('e_contract', 'f_signed', 'g_declined'))]
                if not env.user.has_group('base.group_system'):
                    domain.append(('dealer_portal_user', '=', env.user.id))
                franchise_count = env['franchise.dealer'].sudo().search_count(domain)
                values['franchise_count'] = franchise_count
        return values
