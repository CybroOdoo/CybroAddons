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
# ############################################################################

from odoo import api, models

class OilDashboardEsg(models.TransientModel):
    _inherit = 'oil.dashboard.esg'

    @api.model
    def get_dashboard_data(self):
        """Executes the 'get dashboard data' process within the operational workflow."""
        res = super().get_dashboard_data()
        aros = self.env['oil.aro.obligation'].search([('state', 'in', ('recognized', 'executing', 'hold'))])
        total_liability = sum(aros.mapped('current_liability_balance'))
        
        # Hero card for decommissioning liability
        res['tiles'].append({
            'id': 'esg_aro_liability',
            'label': 'Decommissioning ARO Liability',
            'value': f"${total_liability:,.2f}",
            'icon': 'fa-recycle',
            'color': '#8b5cf6',
            'action': 'oil_erp_aro.action_oil_aro_obligation',
        })
        
        # Detail metric for TCFD reporting
        res['metrics'].append({
            'id': 'esg_tcfd_aro',
            'label': 'TCFD Asset Retirement Liability',
            'value': f"${total_liability:,.2f}",
            'description': 'Estimated future decommissioning liability for environmental remediation and site restoration.',
        })
        return res
