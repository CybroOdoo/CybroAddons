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
from datetime import date
from odoo import api, fields, models


class RenOrder(models.Model):
    """Class for Renewable Energy Order"""
    _name = 'ren.order'
    _description = 'Renewable Energy Order'

    name = fields.Char(string="Order Reference", readonly=True, copy=False,
                       help="Reference for the current order")
    date_of_order = fields.Date(string="Date", default=fields.Date.today, help="Date at which order is confirmed.")
    crm_lead_id = fields.Many2one('crm.lead', string="Lead Source", help="The related CRM lead for this order.",
                                  required=True)
    customer_category_id = fields.Many2one('customer.category', related="crm_lead_id.customer_category_id",
                                           help="Customer Category")
    sales_person_id = fields.Many2one('res.users', string="Responsible", related="crm_lead_id.user_id",
                                      help="Salesperson responsible for this CRM lead.")
    priority = fields.Selection([('0', 'Low'), ('1', 'Medium'), ('2', 'High'), ('3', 'Very High')], string='Priority',
                                related="crm_lead_id.priority", help="Priority level of the CRM lead.")
    company_id = fields.Many2one('res.company', related="crm_lead_id.company_id",
                                 help="The Company associated with the current user.")
    sale_order_id = fields.Many2one('sale.order',
                                    help="The Sale order associated with the current ren order.", readonly=True)
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        readonly=True,
        help="The currency used for this order.",
        default=lambda self: self.env.user.company_id.currency_id.id)
    sale_order_amount = fields.Monetary(string="Sale Amount", related="sale_order_id.amount_total",
                                        help="Total Sale order amount associated with the sale order for the current lead.")
    order_status = fields.Selection([
        ('new', 'New'),
        ('material_order', 'Material Order'),
        ('material_arrived', 'Material Arrived'),
        ('project_installation', 'Project Installation'),
        ('qa_check', 'QA Check'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string="Order Status", default='new', help="Current status of the order.")
    partner_id = fields.Many2one('res.partner', string="Customer", related='crm_lead_id.partner_id', store=True,
                                 readonly=True, help="Customer related to the CRM lead.")
    email = fields.Char(string="Email", related='crm_lead_id.email_from', store=True, readonly=True,
                        help="Email of the customer related to the CRM lead.")
    phone = fields.Char(string="Phone", related='crm_lead_id.phone', store=True, readonly=True,
                        help="Phone number of the customer related to the CRM lead.")
    service_type_id = fields.Many2one('service.type', string="Service Type", related='crm_lead_id.service_type_id',
                                      store=True, readonly=True, help="Type of service related to the CRM lead.")
    service_description = fields.Text(string="Description", related="service_type_id.description",
                                      help="Detailed description of the selected service type.")
    contract_demand_id = fields.Many2one('contract.demand', string="Contract Demand",
                                         related='crm_lead_id.contract_demand_id', store=True, readonly=True,
                                         help="Contract demand related to the CRM lead.")
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
                                    store=True, readonly=True, help="State where the site is located.")
    site_country_id = fields.Many2one('res.country', string="Country", related='crm_lead_id.site_country_id',
                                      store=True, readonly=True, help="Country where the site is located.")
    latitude = fields.Float(string="Latitude", related='crm_lead_id.latitude', store=True, readonly=True,
                            help="Latitude coordinates for the site location.")
    longitude = fields.Float(string="Longitude", related='crm_lead_id.longitude', store=True, readonly=True,
                             help="Longitude coordinates for the site location.")
    site_checklist_line_ids = fields.One2many(
        related='crm_lead_id.site_inspection_id.site_checklist_ids',
        string='Site Checklist',
        help='Checklist items associated with the site inspection.')
    bom_type = fields.Selection(
        selection=[
            ('new', 'New Bill of Material'),
            ('existing', 'Existing Bill of Material')
        ],
        string="BoM Type",
        default='new',
        required=True,
        help="Select 'New Bill of Material' to create a new BoM or 'Existing Bill of Material' to use an existing one.")
    bom_id = fields.Many2one(
        comodel_name='mrp.bom',
        string='Bill of Materials',
        help='Select the Bill of Materials for this project.')
    new_bom_line_ids = fields.One2many(
        comodel_name='customer.bom.line',
        inverse_name='ren_order_id',
        string='BOM Lines',
        help='Add new lines for the temporary Bill of Materials.')
    existing_bom_line_ids = fields.One2many(
        comodel_name='mrp.bom.line',
        related='bom_id.bom_line_ids',
        string='BOM Lines',
        readonly=True,
        help='Product lines from the selected existing Bill of Materials.')
    project_material_cost = fields.Float(
        string='Project Material Cost',
        help='Total cost of materials in the selected BoM.',
        compute="_compute_project_material_cost",
        store=True,
        readonly=True,
        default=0)
    sales_amount = fields.Float(string='Sales Amount', compute='_compute_sales_amount',
                                help="Total amount to be charged for the REN order.")
    create_purchase_order = fields.Boolean(string="Do you want to create purchase order ?",
                                           help="Select this to generate a purchase order for the REN order.")
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order",
                                        help="Purchase order for the REN order.")
    vendor_id = fields.Many2one('res.partner', string="Vendor",
                                help="Vendor to which you want to place purchase order.")
    installation_type = fields.Selection(
        selection=[
            ('internal', 'Internal Team'),
            ('sub_contract', 'Sub Contract')
        ],
        string="Installation Type",
        required=True,
        help="Select 'Internal Team' to assign an internal team or a 'Sub Contract' for installation.",
        default='internal')
    installation_start_date = fields.Date(string="Start Date",
                                          help="Date at which the installation is scheduled to start.")
    installation_end_date = fields.Date(string="End Date",
                                        help="Date on which the installation is planned to be completed.")
    total_days = fields.Integer(string="Total Days", compute="_compute_total_days",
                                help="Total number of days between installation start and end dates.")
    installation_time = fields.Float(
        string='Allocated Time',
        help='Enter time in HH:MM format.')
    price_per_hour = fields.Float(string="Price/Hour", help="Price charged per hour from customer for installation.")
    total_installation_amount = fields.Float(string="Total", help="Total Installation charge.", default=0)
    installation_team_id = fields.Many2one('installation.team', string="Team",
                                           help="Select Installation Team for this Order.")
    installation_team_member_ids = fields.Many2many('installation.team.member', string="Member",
                                                    domain="[('installation_team_id', '=', installation_team_id)]",
                                                    help="Select Team member to which the task must be assigned.")
    installation_task_created = fields.Boolean(string="Created Installation Task",
                                               help="Installation task created or not for the current Order.")
    qa_type = fields.Selection([('internal', 'Internal Team'), ('sub_contract', 'Sub Contract')], string="QA Type",
                               help="Choose 'Internal Team' for assigning QA task to internal team or 'Sub Contract' to assign a subcontractor.",
                               default='internal')
    qa_team_id = fields.Many2one('quality.assurance.team', string="Team",
                                 help="Select QA Team for this Order.")
    qa_team_member_ids = fields.Many2many('quality.assurance.team.member', string="Member",
                                          domain="[('qa_team_id', '=', qa_team_id)]",
                                          help="Select Team member to which the task must be assigned.")
    qa_task_created = fields.Boolean(string="Created QA Task",
                                     help="QA task created or not for the current Order.")
    qa_subcontractor_id = fields.Many2one('res.partner',
                                          string="Subcontractor",
                                          domain=[('is_subcontractor', '=', True)],
                                          help="Choose a subcontractor for QA. Must be marked as a subcontractor.")
    purchase_count = fields.Integer(string="Purchase Count", compute="_compute_purchase_count",
                                    help="Total number of purchase orders linked to this REN order.")
    receipt_count = fields.Integer(string="Receipt Count", compute="_compute_receipt_count",
                                   help="Total number of receipts linked to this REN order.")
    installation_task_count = fields.Integer(string="Installation Task Count",
                                             compute="_compute_installation_task_count",
                                             help="Number of installation task created for the REN order.")
    delivery_count = fields.Integer(string="Delivery Count", compute="_compute_delivery_count",
                                    help="Total number of deliveries linked to this REN order.")
    subcontractor_id = fields.Many2one(
        'res.partner',
        string="Subcontractor",
        domain=[('is_subcontractor', '=', True)],
        help="Select the subcontractor for this task. Only partners marked as subcontractors are available.")
    qa_start_date = fields.Date(string="Start date", help="Start date assigned for QA.")
    qa_end_date = fields.Date(string="End date", help="End date assigned for QA.")
    qa_period = fields.Integer(string="Total Days", help="Total QA period.")
    qa_allocated_time = fields.Float(string="Time Allocated", help="Total time allocated for QA.")
    qa_charge = fields.Float(string="QA Charge", help="Total amount for quality assurance.", default=0)
    qa_task_count = fields.Integer(string="QA Task Count", compute="_compute_qa_task_count",
                                   help="Number of QA tasks created for the REN order.")
    total_cost = fields.Float(string='Total Cost', compute='_compute_total_cost',
                              help="Total cost incurred for the REN order.")
    total_profit_loss = fields.Float(string="Profit & Loss", compute="_compute_total_profit_loss",
                                     help="Profit or loss for this REN order based on sale and cost.")
    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment",
                                   help="Choose equipment for maintenance order.")


    @api.depends('sales_amount', 'total_cost')
    def _compute_total_profit_loss(self):
        """ Function to compute total profit and loss. """
        for order in self:
            order.total_profit_loss = order.sales_amount - order.total_cost

    @api.depends('project_material_cost', 'total_installation_amount', 'qa_charge')
    def _compute_total_cost(self):
        """ Function to compute total expense related to REN order. """
        for order in self:
            order.total_cost = order.project_material_cost + order.total_installation_amount + order.qa_charge

    @api.depends('bom_id.product_tmpl_id.list_price')
    def _compute_sales_amount(self):
        """ Function to compute sale amount for the product. """
        for order in self:
            order.sales_amount = order.bom_id.product_tmpl_id.list_price

    @api.onchange('installation_time', 'price_per_hour')
    def _onchange_installation_time(self):
        """ Function to compute total installation amount. """
        for rec in self:
            rec.total_installation_amount = rec.installation_time * rec.price_per_hour

    def _compute_qa_task_count(self):
        """ Function to compute count of QA task. """
        for rec in self:
            if rec.qa_type == 'internal':
                rec.qa_task_count = self.env['quality.assurance.team.task'].search_count(
                    [('ren_order_id', '=', rec.id)])
            else:
                rec.qa_task_count = self.env['subcontract.quality.assurance.team.task'].search_count(
                    [('ren_order_id', '=', rec.id)])

    @api.onchange('qa_type')
    def _onchange_qa_type(self):
        """ Functon to clear QA team on type change. """
        for rec in self:
            rec.update({
                'qa_team_member_ids': [fields.Command.clear()]
            })
            rec.qa_team_id = False
            rec.qa_subcontractor_id = False

    @api.onchange('installation_type')
    def _onchange_installation_type(self):
        """ Functon to clear installation team on type change. """
        for rec in self:
            rec.update({
                'installation_team_member_ids': [fields.Command.clear()]
            })
            rec.installation_team_id = False
            rec.subcontractor_id = False

    def _compute_delivery_count(self):
        """ Function to compute delivery count for ren order. """
        for rec in self:
            rec.delivery_count = 0
            if rec.sale_order_id:
                rec.delivery_count = self.env['stock.picking'].search_count(
                    [('sale_id', '=', self.sale_order_id.id)])

    def _compute_receipt_count(self):
        """ Function to compute receipt count for ren order purchases. """
        for rec in self:
            rec.receipt_count = self.env['stock.picking'].search_count(
                [('purchase_id', '=', rec.purchase_order_id.id)])

    def _compute_purchase_count(self):
        """ Function to compute purchase count for ren order purchases. """
        for rec in self:
            rec.purchase_count = self.env['purchase.order'].search_count([('ren_order_id', '=', self.id)])

    def _compute_total_days(self):
        """ Function to compute total allocated days for the installation. """
        self.total_days = 0
        if self.installation_start_date and self.installation_end_date:
            self.total_days = (self.installation_end_date - self.installation_start_date).days

    @api.model
    def create(self, vals):
        """ Override create method to handle sequence for Ren order. """
        vals['name'] = self.env['ir.sequence'].next_by_code('ren.order')
        return super(RenOrder, self).create(vals)

    def action_view_map(self):
        """ Recalling method to shop map view from crm_lead model. """
        return self.crm_lead_id.action_view_map(self.latitude, self.longitude)

    @api.onchange('bom_type', 'bom_id')
    def _onchange_bom_type(self):
        """ Function to update BOM product lines. """
        if self.bom_type == 'new':
            self.update({
                'new_bom_line_ids': [fields.Command.clear()]
            })
            self.update({
                'new_bom_line_ids': [fields.Command.create({
                    'product_id': rec.product_id.id,
                    'product_qty': rec.product_qty
                }) for rec in self.bom_id.bom_line_ids]
            })

    @api.depends('bom_type', 'bom_id', 'new_bom_line_ids')
    def _compute_project_material_cost(self):
        """ Function to compute material cost from BOM. """
        for record in self:
            if record.bom_type == 'existing' and record.bom_id:
                total_cost = sum(line.product_qty * line.product_id.lst_price for line in record.existing_bom_line_ids)
            elif record.bom_type == 'new':
                total_cost = sum(line.product_qty * line.product_id.lst_price for line in record.new_bom_line_ids)
            else:
                total_cost = 0.0
            record.project_material_cost = total_cost

    def action_create_purchase_order(self):
        """ Action to create purchase order for the BOM. """
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.vendor_id.id,
            'ren_order_id': self.id,
            'partner_ref': self.name,
            'date_order': fields.Date.today(),
            'order_line': [fields.Command.create({
                'product_id': rec.product_id.id,
                'product_qty': rec.product_qty,
                'price_unit': rec.product_id.lst_price,
            }) for rec in self.new_bom_line_ids]
        })
        self.purchase_order_id = purchase_order.id
        purchase_order.button_confirm()

    def action_view_purchases(self):
        """ Action to view related purchases for Ren order. """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchases Ren Orders',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('ren_order_id', '=', self.id)],
        }

    def action_view_receipt(self):
        """ Action to view related delivery for Ren order purchases. """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Delivery Ren Orders',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('purchase_id', '=', self.purchase_order_id.id)],
        }

    def action_view_delivery(self):
        """ Action to view delivery for the Ren order. """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Customer Delivery Ren Orders',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('sale_id', '=', self.sale_order_id.id)],
        }

    def action_view_installation_task(self):
        """ Action to view related installation tasks for Ren order. """
        if self.installation_type == 'internal':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Installation Task Ren Orders',
                'view_mode': 'tree,form',
                'res_model': 'installation.team.task',
                'domain': [('ren_order_id', '=', self.id)],
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Subcontract Installation Task Ren Orders',
                'view_mode': 'tree,form',
                'res_model': 'subcontract.installation.team.task',
                'domain': [('ren_order_id', '=', self.id)],
            }

    def _compute_installation_task_count(self):
        """ Function to compute number of installation task for the REN order. """
        for rec in self:
            if rec.installation_type == 'internal':
                rec.installation_task_count = self.env['installation.team.task'].search_count(
                    [('ren_order_id', '=', self.id)])
            else:
                rec.installation_task_count = self.env['subcontract.installation.team.task'].search_count(
                    [('ren_order_id', '=', self.id)]
                )

    def action_create_delivery_order(self):
        """ Action to create delivery order for the customer. """
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'order_line': [
                fields.Command.create({
                    'product_id': self.bom_id.product_tmpl_id.product_variant_id.id,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.sale_order_id = sale_order.id
        sale_order.ren_order_id = self.id
        sale_order.action_confirm()

    def action_create_installation_task(self):
        """ Action to create an installation task for the customer. """
        if self.installation_type == 'internal':
            self.env['installation.team.task'].create({
                'ren_order_id': self.id,
            })
        else:
            self.env['subcontract.installation.team.task'].create({
                'ren_order_id': self.id,
            })
        self.installation_task_created = True

    def action_create_qa_task(self):
        """ Action to create qa task for the subcontractor. """
        if self.qa_type == 'internal':
            self.env['quality.assurance.team.task'].create({
                'ren_order_id': self.id
            })
        else:
            self.env['subcontract.quality.assurance.team.task'].create({
                'ren_order_id': self.id
            })

    def action_view_qa_task(self):
        """ Action to return all related QA task for the REN order. """
        if self.qa_type == 'internal':
            return {
                'type': 'ir.actions.act_window',
                'name': 'QA Task Ren Orders',
                'view_mode': 'tree,form',
                'res_model': 'quality.assurance.team.task',
                'domain': [('ren_order_id', '=', self.id)],
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Subcontract QA Task Ren Orders',
                'view_mode': 'tree,form',
                'res_model': 'subcontract.quality.assurance.team.task',
                'domain': [('ren_order_id', '=', self.id)],
            }

    def action_maintenance_request(self):
        """ Function to issue a maintenance request for the product. """
        self.env['maintenance.request'].create({
            'name': self.name,
            'equipment_id': self.equipment_id.id,
            'request_date': date.today(),
            'ren_order_id': self.id,
        })

    def action_material_order(self):
        """Set order status to 'material_order'."""
        self.order_status = 'material_order'

    def action_material_arrived(self):
        """Set order status to 'material_arrived'."""
        self.order_status = 'material_arrived'

    def action_project_installation(self):
        """Set order status to 'project_installation'."""
        self.order_status = 'project_installation'

    def action_qa_check(self):
        """Set order status to 'qa_check'."""
        self.order_status = 'qa_check'

    def action_completed(self):
        """Set order status to 'completed'."""
        self.order_status = 'completed'

    def action_cancel(self):
        """Set order status to 'cancel'."""
        self.order_status = 'cancel'

    def get_dashboard_details(self):
        """Function to return dashboard details ,orm call from dashboard js"""
        ren_orders = self.env['ren.order'].search([])
        site_inspections = self.env['site.inspection'].search([])
        sub_contract_installation = self.env['subcontract.installation.team.task'].search([])
        sub_contract_quality_assurance = self.env['subcontract.quality.assurance.team.task'].search([])
        internal_quality_assurance = self.env['quality.assurance.team.task'].search([])
        internal_installation = self.env['installation.team.task'].search([])

        internal_qa_new_count = len(internal_quality_assurance.filtered(lambda rec: rec.qa_stage == 'new'))
        internal_qa_in_progress_count = len(
            internal_quality_assurance.filtered(lambda rec: rec.qa_stage == 'in_progress'))
        internal_qa_completed_count = len(
            internal_quality_assurance.filtered(lambda rec: rec.qa_stage == 'completed'))
        internal_qa_cancelled_count = len(
            internal_quality_assurance.filtered(lambda rec: rec.qa_stage == 'cancelled'))

        internal_installation_new_count = len(
            internal_installation.filtered(lambda rec: rec.installation_stage == 'new'))
        internal_installation_in_progress_count = len(
            internal_installation.filtered(lambda rec: rec.installation_stage == 'in_progress'))
        internal_installation_completed_count = len(
            internal_installation.filtered(lambda rec: rec.installation_stage == 'completed'))
        internal_installation_cancelled_count = len(
            internal_installation.filtered(lambda rec: rec.installation_stage == 'cancelled'))

        ren_order_count = len(ren_orders)
        material_order_count = self.env['purchase.order'].search_count([('ren_order_id', '!=', False)])
        material_arrival_count = self.env['stock.picking'].search_count([
            ('purchase_id.ren_order_id', '!=', False),
            ('picking_type_id.code', '=', 'incoming'),
            ('state', '=', 'done')
        ])
        maintenance_request_count = self.env['maintenance.request'].search_count([('ren_order_id', '!=', False)])
        sale_order_count = self.env['sale.order'].search_count([('ren_order_id', '!=', False)])
        order_completed_count = len(ren_orders.filtered(lambda rec: rec.order_status == 'completed'))

        site_inspection_new_count = len(site_inspections.filtered(lambda rec: rec.inspection_state == 'new'))
        site_inspection_in_progress_count = len(
            site_inspections.filtered(lambda rec: rec.inspection_state == 'in_progress'))
        site_inspection_completed_count = len(
            site_inspections.filtered(lambda rec: rec.inspection_state == 'completed'))
        site_inspection_cancelled_count = len(
            site_inspections.filtered(lambda rec: rec.inspection_state == 'cancelled'))

        contract_installation_new_count = len(
            sub_contract_installation.filtered(lambda rec: rec.installation_stage == 'new'))
        contract_installation_in_progress_count = len(
            sub_contract_installation.filtered(lambda rec: rec.installation_stage == 'in_progress'))
        contract_installation_completed_count = len(
            sub_contract_installation.filtered(lambda rec: rec.installation_stage == 'completed'))
        contract_installation_cancelled_count = len(
            sub_contract_installation.filtered(lambda rec: rec.installation_stage == 'cancelled'))

        contract_qa_new_count = len(sub_contract_quality_assurance.filtered(lambda rec: rec.qa_stage == 'new'))
        contract_qa_in_progress_count = len(
            sub_contract_quality_assurance.filtered(lambda rec: rec.qa_stage == 'in_progress'))
        contract_qa_completed_count = len(
            sub_contract_quality_assurance.filtered(lambda rec: rec.qa_stage == 'completed'))
        contract_qa_cancelled_count = len(
            sub_contract_quality_assurance.filtered(lambda rec: rec.qa_stage == 'cancelled'))

        return {
            'ren_order_count': ren_order_count,
            'material_order_count': material_order_count,
            'material_arrived_count': material_arrival_count,
            'maintenance_request_count': maintenance_request_count,
            'inspection_new_count': site_inspection_new_count,
            'inspection_in_progress_count': site_inspection_in_progress_count,
            'inspection_completed_count': site_inspection_completed_count,
            'inspection_cancelled_count': site_inspection_cancelled_count,
            'sale_order_count': sale_order_count,
            'order_completed_count': order_completed_count,
            'contract_installation_new_count': contract_installation_new_count,
            'contract_installation_in_progress_count': contract_installation_in_progress_count,
            'contract_installation_completed_count': contract_installation_completed_count,
            'contract_installation_cancelled_count': contract_installation_cancelled_count,
            'contract_qa_new_count': contract_qa_new_count,
            'contract_qa_in_progress_count': contract_qa_in_progress_count,
            'contract_qa_completed_count': contract_qa_completed_count,
            'contract_qa_cancelled_count': contract_qa_cancelled_count,
            'internal_qa_new_count': internal_qa_new_count,
            'internal_qa_in_progress_count': internal_qa_in_progress_count,
            'internal_qa_completed_count': internal_qa_completed_count,
            'internal_qa_cancelled_count': internal_qa_cancelled_count,
            'internal_installation_new_count': internal_installation_new_count,
            'internal_installation_in_progress_count': internal_installation_in_progress_count,
            'internal_installation_completed_count': internal_installation_completed_count,
            'internal_installation_cancelled_count': internal_installation_cancelled_count,
        }
