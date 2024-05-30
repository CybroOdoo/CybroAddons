# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj(<https://www.cybrosys.com>)
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
###########################################################################
from odoo.addons.portal.controllers import portal
from odoo.http import request


class CustomerPortal(portal.CustomerPortal):
    """Class for managing the customer portal functionality 
    of visits management."""
    def _prepare_home_portal_values(self, counters):
        """ Function for finding the number of Visits records """
        values = super()._prepare_home_portal_values(counters)
        if request.env.user.has_group(
                'front_office_management.group_receptionist'):
            if 'visits_count' in counters:
                values['visits_count'] = request.env[
                    'fo.visit'].sudo().search_count([])
        return values
