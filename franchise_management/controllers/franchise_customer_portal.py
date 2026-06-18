# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abbas P(<https://www.cybrosys.com>)
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
"""Franchise customer portal controller"""
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal


class FranchiseCustomerPortal(CustomerPortal):
    """Franchise Customer portal."""

    def _prepare_home_portal_values(self, counters):
        """Preparing franchise count to view in portal."""
        values = super(FranchiseCustomerPortal,
                       self)._prepare_home_portal_values(counters)
        if 'franchise_count' in counters:
            franchise_count = http.request.env[
                'franchise.dealer'].search_count(
                [('state', 'in', ('e_contract', 'f_signed', 'g_declined'))])
            values.update({'franchise_count': franchise_count})
        return values
