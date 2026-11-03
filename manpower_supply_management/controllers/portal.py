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
    """
    This class represents a customer portal.
    It is responsible for preparing home portal values.
    """

    def _prepare_portal_counter_values(self, counter):
        if counter == 'labour_supply_count':
            partner = request.env.user.partner_id
            return ('labour.supply',
                    [('customer_id', 'child_of', [partner.commercial_partner_id.id])],
                    'read')
        return super()._prepare_portal_counter_values(counter)

