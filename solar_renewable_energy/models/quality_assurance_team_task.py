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


class QualityAssuranceTeamTask(models.Model):
    """Class for Quality Assurance Team Task"""
    _name = "quality.assurance.team.task"
    _description = "Quality Assurance Team Task"

    ren_order_id = fields.Many2one('ren.order', help="REN order related to this QA task.")
    qa_type = fields.Selection([('internal', 'Internal Team'), ('sub_contract', 'Sub Contract')], string="QA Type",related="ren_order_id.qa_type")
    qa_stage = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], 'QA Stage', group_expand='_group_expand_qa_states', default='new', required=True, track_visibility='always')
    name = fields.Char(string="Order Reference", required=True, help="Name fo the Installation task.",
                       related="ren_order_id.name")
    qa_team_id = fields.Many2one('quality.assurance.team',
                                           help="Installation team to which this task is assigned.",
                                           related="ren_order_id.qa_team_id")
    qa_team_member_ids = fields.Many2many('quality.assurance.team.member',
                                                    related="ren_order_id.qa_team_member_ids")
    customer_id = fields.Many2one('res.partner', help="Customer who requires this installation task.",
                                  related="ren_order_id.partner_id")
    phone = fields.Char(string="Phone", help="customer's phone number", related="customer_id.phone")
    priority = fields.Selection([('0', 'Low'), ('1', 'Medium'), ('2', 'High'), ('3', 'Very High')], string='Priority',
                                related="ren_order_id.priority")
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
    qa_start_date = fields.Date(string="Start date",
                                          help="Start date assigned for QA.",related="ren_order_id.qa_start_date")
    qa_end_date = fields.Date(string="End date", help="End date assigned for QA.",related="ren_order_id.qa_end_date")
    qa_period = fields.Integer(string="Total Days", help="Total QA period.",related="ren_order_id.qa_period")
    qa_allocated_time = fields.Float(string="Time Allocated", help="Total time allocated for QA.",related="ren_order_id.qa_allocated_time")

    def _group_expand_qa_states(self, states, domain, order):
        """Method ensures all possible selection values for 'qa_stage'
    are included in the groupby, even if no records currently exist in that state."""
        return [key for key, val in type(self).qa_stage.selection]

    def action_in_progress(self):
        """Set the QA stage to 'in_progress'."""
        self.qa_stage = 'in_progress'

    def action_completed(self):
        """Set the QA stage to 'completed'."""
        self.qa_stage = 'completed'
