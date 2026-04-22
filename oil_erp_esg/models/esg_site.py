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
from odoo import api, fields, models


class EsgSite(models.Model):
    """
    Represents a physical operational site or facility (e.g. well site, refinery).
    Acts as a hub for consolidating all ESG-related data for that location.
    """
    _name = 'oil.esg.site'
    _description = 'Oil & Gas Field Site / Facility'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Site Name', required=True, tracking=True,
                       help="Enter the site Name.")
    code = fields.Char(string='Site Code', size=10, required=True,
                       help="Enter the site Code.")
    project_id = fields.Many2one('project.project', string='Project',
                                 domain="[('is_oil_gas_project', '=', True)]",
                                 help="Link this ESG site to an Oil & Gas project.")
    business_segment = fields.Selection([
        ('upstream', 'E&P Operations'),
        ('midstream', 'Pipeline & Transport'),
        ('downstream', 'Refinery Operations'),
        ('corporate', 'Corporate'),
    ], string='Business Segment', required=True, default='upstream', tracking=True,
        help="Choose the business segment this site belongs to.")
    site_type = fields.Selection([
        ('upstream', 'Upstream / Exploration'),
        ('midstream', 'Midstream / Pipeline'),
        ('downstream', 'Downstream / Refinery'),
        ('offshore', 'Offshore Platform'),
        ('terminal', 'Terminal / Storage'),
        ('corporate', 'Corporate Office'),
    ], string='Site Type', required=True, default='upstream', tracking=True,
        help="Choose the site Type.")
    country_id = fields.Many2one('res.country', string='Country',
                                 help="Select the country.")
    state_id = fields.Many2one('res.country.state', string='State/Region',
                               domain="[('country_id', '=', country_id)]",
                               help="Select the state/Region.")
    latitude = fields.Float(string='Latitude', digits=(10, 6),
                            help="Enter the latitude.")
    longitude = fields.Float(string='Longitude', digits=(10, 6),
                             help="Enter the longitude.")
    operator = fields.Char(string='Operator (Legacy)',
                           help="Legacy operator text kept for compatibility.")
    operator_id = fields.Many2one(
        'res.users',
        string='Operator',
        help="Select the internal operator responsible for this site.")

    # Downstream / Manufacturing Links
    workcenter_id = fields.Many2one('mrp.workcenter', string='Workcenter',
                                    help="Link to a manufacturing workcenter for downstream sites.")
    operation_id = fields.Many2one('mrp.routing.workcenter', string='Operation',
                                   help="Link to a specific manufacturing operation.")

    # Midstream Links
    midstream_link_type = fields.Selection([
        ('pipeline', 'Pipeline'),
        ('transfer', 'Inventory Transfer'),
        ('fleet', 'Fleet/Transport'),
    ], string='Midstream Type', help="Choose how this midstream site is linked to operations.")
    delivery_method_id = fields.Many2one('delivery.carrier', string='Pipeline Delivery Method',
                                         help="Link to a pipeline delivery carrier for midstream sites.")
    location_id = fields.Many2one('stock.location', string='Inventory Location',
                                  help="Link to a stock location for transfer-based midstream sites.")
    vehicle_id = fields.Many2one('fleet.vehicle', string='Fleet Vehicle',
                                 help="Link to a fleet vehicle for transport-based midstream sites.")

    production_capacity = fields.Float(string='Production Capacity (boe/day)',
                                       help="Enter the production Capacity (boe/day).")
    active = fields.Boolean(default=True,
                            help="Enable this when active applies.")
    notes = fields.Text(string='Notes', help="Enter the notes.")

    @api.onchange('business_segment')
    def _onchange_business_segment(self):
        """
        Updates the site type default based on the selected business segment
        and resets operational linking fields.
        """
        # Reset all operational fields when segment changes
        self.project_id = False
        self.workcenter_id = False
        self.operation_id = False
        self.midstream_link_type = False
        self.delivery_method_id = False
        self.location_id = False
        self.vehicle_id = False

        if self.business_segment == 'upstream':
            self.site_type = 'upstream'
        elif self.business_segment == 'midstream':
            self.site_type = 'midstream'
        elif self.business_segment == 'downstream':
            self.site_type = 'downstream'
        elif self.business_segment == 'corporate':
            self.site_type = 'corporate'

    @api.onchange('project_id')
    def _onchange_project_id(self):
        """
        Auto-populates site details when a project is selected.
        """
        if self.project_id:
            self.name = self.project_id.name
            # Generate a code if not set
            if not self.code:
                self.code = self.project_id.name[:10].upper()

    emission_ids = fields.One2many('oil.esg.emission', 'site_id',
                                   string='Emissions',
                                   help="Lists the emissions.")
    energy_ids = fields.One2many('oil.esg.energy', 'site_id',
                                 string='Energy Records',
                                 help="Lists the energy Records.")
    water_ids = fields.One2many('oil.esg.water', 'site_id',
                                string='Water Records',
                                help="Lists the water Records.")
    hse_ids = fields.One2many('oil.hse.incident', 'esg_site_id', string='HSE Incidents',
                              help="Lists the HSE Incidents.")

    emission_count = fields.Integer(compute='_compute_counts',
                                    string='Emissions Count',
                                    help="Enter the emissions.")
    energy_count = fields.Integer(compute='_compute_counts', string='Energy',
                                  help="Enter the energy.")
    hse_count = fields.Integer(compute='_compute_counts', string='HSE Count',
                               help="Enter the HSE.")

    @api.depends('emission_ids', 'energy_ids', 'hse_ids')
    def _compute_counts(self):
        """
        Aggregates counts of linked emissions, energy records, and HSE incidents.
        """
        for rec in self:
            rec.emission_count = len(rec.emission_ids)
            rec.energy_count = len(rec.energy_ids)
            rec.hse_count = len(rec.hse_ids)

    def action_view_emissions(self):
        """
        Returns an action to view all GHG emission records for this site.
        """
        return {
            'name': 'GHG Emissions',
            'type': 'ir.actions.act_window',
            'res_model': 'oil.esg.emission',
            'view_mode': 'list,form,pivot,graph',
            'domain': [('site_id', '=', self.id)],
            'context': {'default_site_id': self.id},
        }

    def action_view_energy(self):
        """
        Returns an action to view all energy consumption records for this site.
        """
        return {
            'name': 'Energy Records',
            'type': 'ir.actions.act_window',
            'res_model': 'oil.esg.energy',
            'view_mode': 'list,form,graph',
            'domain': [('site_id', '=', self.id)],
            'context': {'default_site_id': self.id},
        }

    def action_view_hse(self):
        """
        Returns an action to view all HSE incident records for this site.
        """
        return {
            'name': 'HSE Incidents',
            'type': 'ir.actions.act_window',
            'res_model': 'oil.hse.incident',
            'view_mode': 'list,form',
            'domain': [('esg_site_id', '=', self.id)],
            'context': {'default_esg_site_id': self.id},
        }
