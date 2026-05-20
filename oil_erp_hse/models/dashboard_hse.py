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
from datetime import datetime, timedelta

class OilDashboardHse(models.TransientModel):
    _name = 'oil.dashboard.hse'
    _inherit = 'oil.dashboard.base'
    _description = 'HSE Operational Dashboard'

    @api.model
    def get_dashboard_data(self):
        """Compile HSE incident, inspection, permit, and risk data for the dashboard."""
        res = super().get_dashboard_data()
        
        # 1. Incidents
        today = datetime.now()
        last_30_days = today - timedelta(days=30)
        incidents = self.env['oil.hse.incident'].search([])
        recent_incidents = incidents.filtered(lambda r: r.incident_date >= last_30_days)
        critical_incidents = incidents.filtered(lambda r: r.severity in ('high', 'critical') and r.state != 'closed')
        
        # 2. Permits
        permits = self.env['oil.hse.permit'].search([('state', '=', 'approved')])
        expiring_soon = permits.filtered(lambda r: r.end_date and r.end_date <= (today + timedelta(hours=24)))
        
        # 3. Risks
        risks = self.env['oil.hse.risk'].search([])
        high_risks = risks.filtered(lambda r: r.risk_level == 'high')

        # 4. Inspections
        pending_inspections = self.env['oil.hse.inspection'].search([('state', '=', 'draft')])

        # Hero Cards (Tiles)
        res['tiles'] = [
            {
                'id': 'incidents_30d',
                'label': 'Incidents (Last 30 Days)',
                'value': len(recent_incidents),
                'icon': 'fa-exclamation-triangle',
                'color': '#e74c3c',
                'action': 'oil_erp_hse.action_oil_hse_incident',
            },
            {
                'id': 'active_permits',
                'label': 'Active Work Permits',
                'value': len(permits),
                'icon': 'fa-id-card-o',
                'color': '#f39c12',
                'action': 'oil_erp_hse.action_oil_hse_permit',
            },
            {
                'id': 'pending_inspections',
                'label': 'Pending Inspections',
                'value': len(pending_inspections),
                'icon': 'fa-check-square-o',
                'color': '#3498db',
                'action': 'oil_erp_hse.action_oil_hse_inspection',
            },
            {
                'id': 'high_risks',
                'label': 'High Risk Assessments',
                'value': len(high_risks),
                'icon': 'fa-shield',
                'color': '#e67e22',
                'action': 'oil_erp_hse.action_oil_hse_risk',
            },
        ]

        # Charts
        # Incident Severity Distribution
        severity_counts = {}
        for incident in incidents:
            sev = incident.severity
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
        res['charts'].append({
            'id': 'incident_severity',
            'title': 'Incident Severity',
            'type': 'pie',
            'data': {
                'labels': ['Critical', 'High', 'Medium', 'Low'],
                'datasets': [{
                    'data': [
                        severity_counts.get('critical', 0),
                        severity_counts.get('high', 0),
                        severity_counts.get('medium', 0),
                        severity_counts.get('low', 0),
                    ],
                    'backgroundColor': ['#C0392B', '#E67E22', '#F1C40F', '#27AE60'],
                }]
            }
        })

        # Risk Level Distribution
        risk_counts = {}
        for risk in risks:
            rl = risk.risk_level
            risk_counts[rl] = risk_counts.get(rl, 0) + 1

        res['charts'].append({
            'id': 'risk_levels',
            'title': 'Risk Distribution',
            'type': 'bar',
            'data': {
                'labels': ['High Risk', 'Medium Risk', 'Low Risk'],
                'datasets': [{
                    'label': 'Assessments',
                    'data': [
                        risk_counts.get('high', 0),
                        risk_counts.get('medium', 0),
                        risk_counts.get('low', 0),
                    ],
                    'backgroundColor': '#2c3e50',
                }]
            }
        })

        # Highlights
        res['highlights'] = [
            {
                'id': 'critical_watchlist',
                'title': 'Critical Incidents',
                'items': [
                    {'label': r.name, 'value': r.severity.upper()} for r in critical_incidents[:5]
                ],
            },
            {
                'id': 'permit_expiry',
                'title': 'Permit Watchlist',
                'items': [
                    {'label': r.name, 'value': 'Expiring Soon'} for r in expiring_soon[:5]
                ],
            },
            {
                'id': 'high_risk_zones',
                'title': 'High Risk Assessments',
                'items': [
                    {'label': r.name, 'value': 'High Risk'} for r in high_risks[:5]
                ],
            }
        ]

        return res
