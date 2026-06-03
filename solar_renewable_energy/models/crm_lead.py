# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amrithesh K (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class CrmLead(models.Model):
    """Inherited to add solar renewable energy related fields and functions."""
    _inherit = 'crm.lead'

    customer_category_id = fields.Many2one('customer.category', string="Customer Category",
                                           help="Select the category of the customer.")
    contract_demand_id = fields.Many2one('contract.demand', string="Contract Demand",
                                         help="Specify the contract demand for the customer.")
    connection_type = fields.Selection([
        ('single_phase', 'Single Phase'),
        ('three_phase', '3 Phase')
    ], string="Connection Type", help="Choose the type of electrical connection.")
    service_type_id = fields.Many2one('service.type', string="Service Type",
                                      help="Select the type of service for the customer.")
    existing_supply_volt = fields.Float(string="Existing Supply Voltage",
                                        help="Enter the existing supply voltage in volts.")
    consumer_no = fields.Integer(string="Consumer Number", help="Enter the consumer number for the customer.")
    monthly_electricity_bill = fields.Float(string="Monthly Electricity Bill",
                                            help="Enter the average monthly electricity bill amount.")
    site_usage = fields.Char(string="Site Usage", help="Describe how the site is being used.")
    property_type_id = fields.Many2one('property.type', string="Type of Property",
                                       help="Specify the type of property for the site.")
    age_of_property = fields.Integer(string="Age of Property", help="Enter the age of the property in years.")
    site_street1 = fields.Char(string="Street 1", help="Enter the first line of the site's street address.")
    site_street2 = fields.Char(string="Street 2", help="Enter the second line of the site's street address.")
    site_city = fields.Char(string="City", help="Enter the city where the site is located.")
    site_state_id = fields.Many2one('res.country.state', string="State",
                                    help="Select the state where the site is located.")
    site_country_id = fields.Many2one('res.country', string="Country",
                                      help="Select the country where the site is located.")
    latitude = fields.Float(string="Latitude", help="Enter the latitude coordinates for the site location.")
    longitude = fields.Float(string="Longitude", help="Enter the longitude coordinates for the site location.")
    sale_quotation_id = fields.Many2one('sale.order', string="Sale Quotation", help="Sale order related to this field.")
    site_inspection_id = fields.Many2one('site.inspection', string="Site Inspections.",
                                         help="Site inspections related to this lead")
    ren_order_id = fields.Many2one('ren.order', string="Ren Order", help="Ren Orders created for this lead.",
                                   readonly=True)
    site_inspection_count = fields.Integer('site.inspection', compute="_compute_site_inspection_count",help='number '
                                                                                                            'of site '
                                                                                                            'inspections')
    ren_order_count = fields.Integer('ren.order', compute="_compute_ren_order_count",help='number of renewable orders.')

    def _compute_site_inspection_count(self):
        """ Function to compute site inspection count for the lead. """
        for rec in self:
            rec.site_inspection_count = self.env['site.inspection'].search_count([('crm_lead_id', '=', rec.id)])

    def _compute_ren_order_count(self):
        """ Function to compute ren order count for the lead. """
        for rec in self:
            rec.ren_order_count = self.env['ren.order'].search_count([('crm_lead_id', '=', rec.id)])

    def action_view_map(self, latitude=None, longitude=None):
        """ Action to redirect to google map site location. """
        lat = latitude or self.latitude
        long = longitude or self.longitude
        url = f"https://www.google.com/maps/search/?api=1&query={lat},{long}"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def action_view_site_inspection(self):
        """ Action to view related site inspection. """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Site Inspections',
            'view_mode': 'tree,form',
            'res_model': 'site.inspection',
            'domain': [('crm_lead_id', '=', self.id)],
        }

    def action_view_ren_order(self):
        """ Action to view related ren orders. """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ren Orders',
            'view_mode': 'tree,form',
            'res_model': 'ren.order',
            'domain': [('crm_lead_id', '=', self.id)],
        }

    def action_create_site_inspection(self):
        """ Action to return wizard for site inspection creation. """
        return {
            'name': 'Create Site Inspection',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'site.inspection.assignment',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
                'default_service_type_id': self.service_type_id.id
            },
        }

    def action_create_ren_order(self):
        """ action to create renewable order for the lead. """
        order = self.env['ren.order'].create({
            'crm_lead_id': self.id,
        })
        self.ren_order_id = order.id
