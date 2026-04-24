# -*- coding: utf-8 -*-
from odoo import models, fields, api

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
    _name = 'oil.dashboard.upstream'
    _inherit = 'oil.dashboard.base'
    _description = 'Upstream Dashboard'

class OilDashboardMidstream(models.TransientModel):
    _name = 'oil.dashboard.midstream'
    _inherit = 'oil.dashboard.base'
    _description = 'Midstream Dashboard'

class OilDashboardDownstream(models.TransientModel):
    _name = 'oil.dashboard.downstream'
    _inherit = 'oil.dashboard.base'
    _description = 'Downstream Dashboard'
