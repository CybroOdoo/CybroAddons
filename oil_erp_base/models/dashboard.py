# -*- coding: utf-8 -*-
#############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, models

class OilDashboardBase(models.AbstractModel):
    _name = 'oil.dashboard.base'
    _description = 'Oil ERP Dashboard Base'

    @api.model
    def get_dashboard_data(self):
        """ Returns data for the dashboard. Should be overridden by each operation module. """
        return {
            'tiles': [],
            'charts': [],
            'metrics': [],
            'highlights': [],
        }

class OilDashboardUpstream(models.TransientModel):
    """Upstream operations dashboard aggregating exploration, drilling, and production data."""
    _name = 'oil.dashboard.upstream'
    _inherit = 'oil.dashboard.base'
    _description = 'Upstream Dashboard'

class OilDashboardMidstream(models.TransientModel):
    """Midstream operations dashboard aggregating pipeline and transfer logistics data."""
    _name = 'oil.dashboard.midstream'
    _inherit = 'oil.dashboard.base'
    _description = 'Midstream Dashboard'

class OilDashboardDownstream(models.TransientModel):
    """Downstream operations dashboard aggregating refinery and manufacturing data."""
    _name = 'oil.dashboard.downstream'
    _inherit = 'oil.dashboard.base'
    _description = 'Downstream Dashboard'
