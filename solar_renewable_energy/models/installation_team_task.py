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


class InstallationTeamTask(models.Model):
    """Class for solar installation team task"""
    _name = "installation.team.task"
    _description = "Installation Team Task"

    ren_order_id = fields.Many2one('ren.order', help="REN order related to this installation task.")
    installation_stage = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], 'Installation Stage', group_expand='_group_expand_installation_states', default='new', required=True,
        track_visibility='always')
    name = fields.Char(string="Order Reference", required=True, help="Name fo the Installation task.",
                       related="ren_order_id.name")
    installation_team_id = fields.Many2one('installation.team',
                                           help="Installation team to which this task is assigned.",
                                           related="ren_order_id.installation_team_id")
    installation_team_member_ids = fields.Many2many('installation.team.member',
                                                    help="Team member to which this task is assigned.",
                                                    related="ren_order_id.installation_team_member_ids")
    customer_id = fields.Many2one('res.partner', help="Customer who requires this installation task.",
                                  related="ren_order_id.partner_id")
    phone = fields.Char(string="Phone", help="customer's phone number", related="customer_id.phone")
    priority = fields.Selection([('0', 'Low'), ('1', 'Medium'), ('2', 'High'), ('3', 'Very High')], string='Priority',
                                related="ren_order_id.priority")
    service_type_id = fields.Many2one('service.type', string="Service Type", store=True, readonly=True,
                                      help="Type of service related to this installation.",
                                      related="ren_order_id.service_type_id")
    service_description = fields.Text(string="Description", related="ren_order_id.service_description")
    contract_demand_id = fields.Many2one('contract.demand', string="Contract Demand",
                                         store=True, readonly=True,
                                         help="Contract demand for the order.",
                                         related="ren_order_id.contract_demand_id")
    site_usage = fields.Char(string="Site Usage", store=True, readonly=True,
                             help="Description of how the site is being used.", related="ren_order_id.site_usage")
    property_type_id = fields.Many2one('property.type', string="Type of Property",
                                       store=True, readonly=True,
                                       help="Type of property.", related="ren_order_id.property_type_id")
    age_of_property = fields.Integer(string="Age of Property", store=True,
                                     readonly=True, help="Age of the property in years.",
                                     related="ren_order_id.age_of_property")
    latitude = fields.Float(string="Latitude", store=True, readonly=True,
                            help="Latitude coordinates for the site location.", related="ren_order_id.latitude")
    longitude = fields.Float(string="Longitude", store=True, readonly=True,
                             help="Longitude coordinates for the site location.", related="ren_order_id.longitude")
    bom_ids = fields.One2many(
        comodel_name='customer.bom.line',
        related='ren_order_id.new_bom_line_ids',
        string='BOM Lines',
        help='Add new lines for the temporary Bill of Materials.')
    installation_start_date = fields.Date(string="Start date",
                                          help="Start date assigned for installation.",
                                          related="ren_order_id.installation_start_date")
    installation_end_date = fields.Date(string="End date", help="End date assigned for installation.",
                                        related="ren_order_id.installation_end_date")
    installation_period = fields.Integer(string="Total Days", help="Total installation period.",
                                         related="ren_order_id.total_days")
    allocated_time = fields.Float(string="Time Allocated", help="Total time allocated for installation.",
                                  related="ren_order_id.total_installation_amount")

    def _group_expand_installation_states(self, states, domain, order):
        """Ensures all possible selection values for 'installation_stage'
    are included in the kanban view."""
        return [key for key, val in type(self).installation_stage.selection]

    def action_in_progress(self):
        """Set the installation stage to 'in_progress'."""
        self.installation_stage = 'in_progress'

    def action_completed(self):
        """Set the installation stage to 'completed'."""
        self.installation_stage = 'completed'
