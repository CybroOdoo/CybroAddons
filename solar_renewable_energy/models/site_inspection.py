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


class SiteInspection(models.Model):
    """Class for site inspection"""
    _name = "site.inspection"
    _description = "Site Inspection"

    name = fields.Char(string="Site Name", required=True, help="Name of the site", related="crm_lead_id.name")
    inspection_state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string="Inspection State", help="Current status of inspection.", default="new")
    crm_lead_id = fields.Many2one('crm.lead', string="Related CRM",
                                  help="Lead from which the inspection has been issued")
    survey_team_id = fields.Many2one('survey.team', string="Survey Team", help="survey team ")
    survey_team_member_id = fields.Many2one('survey.team.member', string="Survey Team Member")
    date_of_inspection = fields.Date(string="Date of Inspection", help="Date assigned for inspection")
    partner_id = fields.Many2one('res.partner', string="Customer", related='crm_lead_id.partner_id', store=True,
                                 readonly=True, help="Customer related to the CRM lead.")
    email = fields.Char(string="Email", related='crm_lead_id.email_from', store=True, readonly=True,
                        help="Email of the customer related to the CRM lead.")
    phone = fields.Char(string="Phone", related='crm_lead_id.phone', store=True, readonly=True,
                        help="Phone number of the customer related to the CRM lead.")
    customer_category_id = fields.Many2one('customer.category', string="Customer Category",
                                           related='crm_lead_id.customer_category_id', store=True, readonly=True,
                                           help="Category of the customer related to the CRM lead.")
    service_type_id = fields.Many2one('service.type', string="Service Type", related='crm_lead_id.service_type_id',
                                      store=True, readonly=True, help="Type of service related to the CRM lead.")
    contract_demand_id = fields.Many2one('contract.demand', string="Contract Demand",
                                         related='crm_lead_id.contract_demand_id', store=True, readonly=True,
                                         help="Contract demand related to the CRM lead.")
    connection_type = fields.Selection([
        ('single_phase', 'Single Phase'),
        ('three_phase', '3 Phase')
    ], string="Connection Type", related='crm_lead_id.connection_type', store=True, readonly=True,
        help="Type of electrical connection related to the CRM lead.")
    existing_supply_volt = fields.Float(string="Existing Supply Voltage",
                                        related='crm_lead_id.existing_supply_volt', store=True, readonly=True,
                                        help="Existing supply voltage in volts related to the CRM lead.")
    consumer_no = fields.Integer(string="Consumer Number", related='crm_lead_id.consumer_no', store=True,
                                 readonly=True, help="Consumer number related to the CRM lead.")
    monthly_electricity_bill = fields.Float(string="Monthly Electricity Bill",
                                            related='crm_lead_id.monthly_electricity_bill', store=True,
                                            readonly=True,
                                            help="Average monthly electricity bill amount related to the CRM lead.")
    site_usage = fields.Char(string="Site Usage", related='crm_lead_id.site_usage', store=True, readonly=True,
                             help="Description of how the site is being used.")
    property_type_id = fields.Many2one('property.type', string="Type of Property",
                                       related='crm_lead_id.property_type_id', store=True, readonly=True,
                                       help="Type of property.")
    age_of_property = fields.Integer(string="Age of Property", related='crm_lead_id.age_of_property', store=True,
                                     readonly=True, help="Age of the property in years.")
    site_street1 = fields.Char(string="Street 1", related='crm_lead_id.site_street1', store=True, readonly=True,
                               help="First line of the site's street address.")
    site_street2 = fields.Char(string="Street 2", related='crm_lead_id.site_street2', store=True, readonly=True,
                               help="Second line of the site's street address.")
    site_city = fields.Char(string="City", related='crm_lead_id.site_city', store=True, readonly=True,
                            help="City where the site is located.")
    site_state_id = fields.Many2one('res.country.state', string="State", related='crm_lead_id.site_state_id',
                                    store=True, readonly=True,
                                    help="State where the site is located.")
    site_country_id = fields.Many2one('res.country', string="Country", related='crm_lead_id.site_country_id',
                                      store=True, readonly=True,
                                      help="Country where the site is located.")
    latitude = fields.Float(string="Latitude", related='crm_lead_id.latitude', store=True, readonly=True,
                            help="Latitude coordinates for the site location.")
    longitude = fields.Float(string="Longitude", related='crm_lead_id.longitude', store=True, readonly=True,
                             help="Longitude coordinates for the site location.")
    company_id = fields.Many2one('res.company', string="Company", related='crm_lead_id.company_id', store=True,
                                 readonly=True)
    user_id = fields.Many2one('res.users', string="Salesperson", related='crm_lead_id.user_id', store=True,
                              readonly=True, help="Salesperson responsible for the CRM lead.")
    survey_images_ids = fields.Many2many('ir.attachment',
                                         string="Add",
                                         help="Upload images related to the site survey.",
                                         relation='site_inspection_ir_attachment_rel',
                                         column1='site_inspection_id',
                                         column2='attachment_id',
                                         domain="[('mimetype', 'ilike', 'image/')]")
    site_checklist_ids = fields.One2many(
        'site.checklist.line',
        'site_checklist_id',
        string="Checklist Lines",
        help="List of checklist items that need to be assessed during the site inspection.")
    site_remark = fields.Html(string="Site Remark", help="Remarks about the site.")

    def action_set_in_progress(self):
        """ Method to set the state to 'in_progress'. """
        self.inspection_state = 'in_progress'

    def action_set_completed(self):
        """ Method to set the state to 'completed'. """
        self.inspection_state = 'completed'

    def action_cancel(self):
        """ Method to set the state to 'Cancelled'. """
        self.inspection_state = 'cancelled'

    def action_view_map(self):
        """ Recalling method to shop map view from crm_lead model. """
        return self.crm_lead_id.action_view_map(self.latitude, self.longitude)
