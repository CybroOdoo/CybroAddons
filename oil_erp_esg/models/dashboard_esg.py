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
from datetime import datetime

class OilDashboardEsg(models.TransientModel):
    _name = 'oil.dashboard.esg'
    _inherit = 'oil.dashboard.base'
    _description = 'ESG Performance Dashboard'

    @api.model
    def get_dashboard_data(self):
        """Compile ESG metrics including emissions, energy, water, workforce, and compliance data for dashboard display."""
        res = super().get_dashboard_data()
        
        # 1. Emissions Data
        emissions = self.env['oil.esg.emission'].search([])
        total_co2e = sum(emissions.mapped('quantity_co2e'))
        
        # 2. Energy Data
        energy = self.env['oil.esg.energy'].search([('energy_type', '=', 'consumed')])
        total_gj = sum(energy.mapped('quantity_gj'))
        production_boe = sum(energy.mapped('production_boe'))
        energy_intensity = (total_gj / production_boe) if production_boe else 0.0
        renewable_energy = sum(energy.filtered(lambda r: r.is_renewable).mapped('quantity_gj'))
        renewable_ratio = (renewable_energy / total_gj * 100) if total_gj else 0.0
        
        # 3. Water & Waste Data
        water_records = self.env['oil.esg.water'].search([])
        water_withdrawal = sum(water_records.filtered(lambda r: r.record_type == 'water_withdrawal').mapped('volume_m3'))
        water_recycled = sum(water_records.filtered(lambda r: r.record_type == 'water_recycled').mapped('volume_m3'))
        water_recycle_rate = (water_recycled / water_withdrawal * 100) if water_withdrawal else 0.0
        
        hazardous_waste = sum(water_records.filtered(lambda r: r.record_type == 'waste_hazardous').mapped('quantity_tonnes'))
        non_hazardous_waste = sum(water_records.filtered(lambda r: r.record_type == 'waste_non_hazardous').mapped('quantity_tonnes'))
        
        # 4. Workforce & Social Data
        workforce = self.env['oil.esg.workforce'].search([], order='date_to desc', limit=1)
        total_emp = workforce.total_employees or 0
        local_hire_ratio = workforce.local_hire_ratio or 0.0
        grievance_rate = workforce.grievance_resolution_rate or 0.0
        community_invest = workforce.community_investment or 0.0
        training_hrs = workforce.training_hours or 0.0
        
        # 5. Compliance Data
        compliance = self.env['oil.esg.compliance'].search([])
        total_compliance = len(compliance)
        compliant_count = len(compliance.filtered(lambda r: r.status == 'compliant'))
        compliance_rate = (compliant_count / total_compliance * 100) if total_compliance else 0.0
        open_gaps = len(compliance.filtered(lambda r: r.status == 'gap'))
        
        # 6. Initiatives Data
        initiatives = self.env['oil.esg.initiative'].search([])
        active_initiatives = len(initiatives.filtered(lambda r: r.state == 'inprogress'))

        # Hero Cards (Tiles)
        res['tiles'].extend([
            {
                'id': 'esg_emissions',
                'label': 'Total Emissions (tCO2e)',
                'value': f"{total_co2e:,.2f}",
                'icon': 'fa-cloud',
                'color': '#ef4444',
                'action': 'oil_erp_esg.action_oil_esg_emission',
            },
            {
                'id': 'esg_energy_intensity',
                'label': 'Energy Intensity (GJ/BOE)',
                'value': f"{energy_intensity:.2f}",
                'icon': 'fa-bolt',
                'color': '#f59e0b',
                'action': 'oil_erp_esg.action_oil_esg_energy',
            },
            {
                'id': 'esg_water_recycle',
                'label': 'Water Recycle Rate',
                'value': f"{water_recycle_rate:.1f}%",
                'icon': 'fa-tint',
                'color': '#3b82f6',
                'action': 'oil_erp_esg.action_oil_esg_water',
            },
            {
                'id': 'esg_compliance_rate',
                'label': 'Compliance Rate',
                'value': f"{compliance_rate:.1f}%",
                'icon': 'fa-shield',
                'color': '#10b981',
                'action': 'oil_erp_esg.action_oil_esg_compliance',
            },
            {
                'id': 'esg_female_ratio',
                'label': 'Local Hire Ratio',
                'value': f"{local_hire_ratio:.1f}%",
                'icon': 'fa-users',
                'color': '#06b6d4',
                'action': 'oil_erp_esg.action_oil_esg_workforce',
            },
            {
                'id': 'esg_active_projects',
                'label': 'Active Initiatives',
                'value': active_initiatives,
                'icon': 'fa-rocket',
                'color': '#8b5cf6',
                'action': 'oil_erp_esg.action_oil_esg_initiative',
            },
        ])

        # Charts
        # 1. Emissions by Scope
        scope_data = {}
        for r in emissions:
            scope_data[r.scope] = scope_data.get(r.scope, 0) + r.quantity_co2e
            
        res['charts'].append({
            'id': 'esg_emissions_scope',
            'title': 'Emissions by Scope',
            'type': 'pie',
            'width': 6,
            'data': {
                'labels': ['Scope 1', 'Scope 2', 'Scope 3'],
                'datasets': [{
                    'data': [
                        scope_data.get('scope1', 0),
                        scope_data.get('scope2', 0),
                        scope_data.get('scope3', 0),
                    ],
                    'backgroundColor': ['#ef4444', '#f97316', '#eab308'],
                }]
            }
        })

        # 2. Water Management
        res['charts'].append({
            'id': 'esg_water_mgmt',
            'title': 'Water: Withdrawal vs Recycled (m³)',
            'type': 'bar',
            'width': 6,
            'data': {
                'labels': ['Withdrawal', 'Recycled'],
                'datasets': [{
                    'label': 'Volume m³',
                    'data': [water_withdrawal, water_recycled],
                    'backgroundColor': ['#3b82f6', '#10b981'],
                }]
            }
        })

        # 3. Energy by Source
        source_data = {}
        for r in energy:
            source_data[r.energy_source] = source_data.get(r.energy_source, 0) + r.quantity_gj
            
        sources = sorted(source_data.keys(), key=lambda x: source_data[x], reverse=True)[:5]
        res['charts'].append({
            'id': 'esg_energy_source',
            'title': 'Top 5 Energy Sources (GJ)',
            'type': 'bar',
            'width': 12,
            'data': {
                'labels': [s.replace('_', ' ').capitalize() for s in sources],
                'datasets': [{
                    'label': 'Energy (GJ)',
                    'data': [source_data[s] for s in sources],
                    'backgroundColor': '#475569',
                }]
            }
        })

        # Metrics (Detail Cards)
        res['metrics'].extend([
            {
                'id': 'esg_waste',
                'label': 'Waste Production',
                'value': f"{hazardous_waste + non_hazardous_waste:,.1f} t",
                'description': f"Hazardous: {hazardous_waste:,.1f} t | Non-Hazardous: {non_hazardous_waste:,.1f} t",
            },
            {
                'id': 'esg_training',
                'label': 'Workforce Development',
                'value': f"{training_hrs:,.0f} hrs",
                'description': f"Total training hours provided across {total_emp} employees.",
            },
            {
                'id': 'esg_community',
                'label': 'Social Impact',
                'value': f"${community_invest:,.0f}",
                'description': f"Total community investment and social responsibility spend.",
            },
            {
                'id': 'esg_grievance',
                'label': 'Grievance Resolution',
                'value': f"{grievance_rate:.1f}%",
                'description': "Percentage of community grievances resolved within the period.",
            },
        ])

        # Highlights
        # Top Emitting Sites
        site_emissions = {}
        for r in emissions:
            site_emissions[r.site_id.name] = site_emissions.get(r.site_id.name, 0) + r.quantity_co2e
        top_sites = sorted(site_emissions.items(), key=lambda x: x[1], reverse=True)[:5]

        # Upcoming Deadlines
        today = datetime.now().date()
        upcoming_deadlines = compliance.filtered(lambda r: r.deadline_date and r.deadline_date >= today).sorted('deadline_date')

        res['highlights'].extend([
            {
                'id': 'esg_top_emitters',
                'title': 'High Emission Facilities',
                'items': [
                    {'label': name, 'value': f"{val:,.0f} tCO2e"} for name, val in top_sites
                ],
            },
            {
                'id': 'esg_compliance_watchlist',
                'title': 'Compliance Watchlist',
                'items': [
                    {'label': r.name, 'value': r.deadline_date.strftime('%Y-%m-%d')} for r in upcoming_deadlines[:5]
                ],
            }
        ])

        return res
