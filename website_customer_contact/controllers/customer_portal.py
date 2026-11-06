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
from odoo.addons.portal.controllers import portal
from odoo.http import request


class CustomerPortal(portal.CustomerPortal):
    """"Class to create a portal to website"""

    def _prepare_portal_counter_values(self, counter):
        """"Function to super and pass value to portal"""
        if counter == 'contact_count':
            return 'res.partner', [('parent_id', '=', request.env.user.partner_id.id)], 'read'
        return super()._prepare_portal_counter_values(counter)

    def _prepare_home_portal_values(self, counters):
        """"Function to super and pass value to portal"""
        values = super()._prepare_home_portal_values(counters) if hasattr(super(), '_prepare_home_portal_values') else {}
        if 'contact_count' in counters:
            values['contact_count'] = request.env['res.partner'] \
                .sudo().search_count(
                [('parent_id', '=', request.env.user.partner_id.id)])
        return values

