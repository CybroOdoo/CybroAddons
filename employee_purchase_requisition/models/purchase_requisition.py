# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vishnu P(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
""" Purchase Requisition model"""
from odoo import models, fields, api


class PurchaseRequisition(models.Model):
    """ Model for storing purchase requisition """
    _name = 'employee.purchase.requisition'
    _description = 'Purchase Requisition'
    _inherit = "mail.thread", "mail.activity.mixin"

    name = fields.Char(string="Reference No", readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  required=True, help='Employee')
    dept_id = fields.Many2one('hr.department', string='Department',
                              related='employee_id.department_id', store=True,
                              help='Department')
    user_id = fields.Many2one('res.users', string='Requisition Responsible',
                              required=True,
                              help='Requisition responsible user')
    requisition_date = fields.Date(string="Requisition Date",
                                   default=lambda self: fields.Date.today(),
                                   help='Date of Requisition')
    receive_date = fields.Date(string="Received Date", readonly=True,
                               help='Receive Date')
    requisition_deadline = fields.Date(string="Requisition Deadline",
                                       help="End date of Purchase requisition")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 help='Company')
    requisition_order_ids = fields.One2many('requisition.order',
                                            'requisition_product_id',
                                            required=True)
    confirm_id = fields.Many2one('res.users', string='Confirmed By',
                                 default=lambda self: self.env.uid,
                                 readonly=True,
                                 help='User who Confirmed the requisition.')
    manager_id = fields.Many2one('res.users', string='Department Manager',
                                 readonly=True, help='Department Manager')
    requisition_head_id = fields.Many2one('res.users', string='Approved By',
                                          readonly=True,
                                          help='User who approved the requisition.')
    rejected_user_id = fields.Many2one('res.users', string='Rejected By',
                                       readonly=True,
                                       help='user who rejected the requisition')
    confirmed_date = fields.Date(string='Confirmed Date', readonly=True,
                                 help='Date of Requisition Confirmation')
    department_approval_date = fields.Date(string='Department Approval Date',
                                           readonly=True,
                                           help='Department Approval Date')
    approval_date = fields.Date(string='Approved Date', readonly=True,
                                help='Requisition Approval Date')
    reject_date = fields.Date(string='Rejection Date', readonly=True,
                              help='Requisition Rejected Date')
    source_location_id = fields.Many2one('stock.location',
                                         string='Source Location',
                                         help='Source location of requisition.')
    destination_location_id = fields.Many2one('stock.location',
                                              string="Destination Location",
                                              help='Destination location of requisition.')
    delivery_type_id = fields.Many2one('stock.picking.type',
                                       string='Delivery To',
                                       help='Type of Delivery.')
    internal_picking_id = fields.Many2one('stock.picking.type',
                                          string="Internal Picking")
    requisition_description = fields.Text(string="Reason For Requisition")
    purchase_count = fields.Integer(string='Purchase Count')
    internal_transfer_count = fields.Integer(string='Internal Transfer count')
    state = fields.Selection(
        [('new', 'New'),
         ('waiting_department_approval', 'Waiting Department Approval'),
         ('waiting_head_approval', 'Waiting Head Approval'),
         ('approved', 'Approved'),
         ('purchase_order_created', 'Purchase Order Created'),
         ('received', 'Received'),
         ('cancelled', 'Cancelled')],
        default='new', copy=False, tracking=True)

    @api.model
    def create(self, vals):
        """generate purchase requisition sequence"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'employee.purchase.requisition') or 'New'
        result = super(PurchaseRequisition, self).create(vals)
        return result

    def action_confirm_requisition(self):
        """confirm purchase requisition"""
        self.source_location_id = self.employee_id.department_id.department_location_id.id
        self.destination_location_id = self.employee_id.employee_location_id.id
        self.delivery_type_id = self.source_location_id.warehouse_id.in_type_id.id
        self.internal_picking_id = self.source_location_id.warehouse_id.int_type_id.id
        self.write({'state': 'waiting_department_approval'})
        self.confirm_id = self.env.uid
        self.confirmed_date = fields.Date.today()

    def action_department_approval(self):
        """approval from department"""
        self.write({'state': 'waiting_head_approval'})
        self.manager_id = self.env.uid
        self.department_approval_date = fields.Date.today()

    def action_department_cancel(self):
        """cancellation from department """
        self.write({'state': 'cancelled'})
        self.rejected_user_id = self.env.uid
        self.reject_date = fields.Date.today()

    def action_head_approval(self):
        """approval from department head"""
        self.write({'state': 'approved'})
        self.requisition_head_id = self.env.uid
        self.approval_date = fields.Date.today()

    def action_head_cancel(self):
        """cancellation from department head"""
        self.write({'state': 'cancelled'})
        self.rejected_user_id = self.env.uid
        self.reject_date = fields.Date.today()

    def action_create_purchase_order(self):
        """create purchase order and internal transfer"""
        for rec in self.requisition_order_ids:
            if rec.requisition_type == 'internal_transfer':
                self.env['stock.picking'].create({
                    'location_id': self.source_location_id.id,
                    'location_dest_id': self.destination_location_id.id,
                    'picking_type_id': self.internal_picking_id.id,
                    'requisition_order': self.name,
                    'move_ids_without_package': [(0, 0, {
                        'name': rec.product_id.name,
                        'product_id': rec.product_id.id,
                        'product_uom': rec.product_id.uom_id,
                        'product_uom_qty': rec.quantity,
                        'location_id': self.source_location_id.id,
                        'location_dest_id': self.destination_location_id.id,
                    })]
                })
            else:
                self.env['purchase.order'].create({
                    'partner_id': self.employee_id.work_contact_id.id,
                    'requisition_order': self.name,
                    "order_line": [(0, 0, {
                        'product_id': rec.product_id.id,
                        'product_qty': rec.quantity,
                    })]})
        self.write({'state': 'purchase_order_created'})
        self.purchase_count = self.env['purchase.order'].search_count([
            ('requisition_order', '=', self.name)])
        self.internal_transfer_count = self.env['stock.picking'].search_count([
            ('requisition_order', '=', self.name)])

    def action_receive(self):
        """receive purchase requisition"""
        self.write({'state': 'received'})
        self.receive_date = fields.Date.today()

    def get_purchase_order(self):
        """purchase order smart button view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('requisition_order', '=', self.name)],
        }

    def get_internal_transfer(self):
        """internal transfer smart tab view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Internal Transfers',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('requisition_order', '=', self.name)],
        }

    def action_print_report(self):
        """print purchase requisition report"""
        data = {
            'employee': self.employee_id.name,
            'records': self.read(),
            'order_ids': self.requisition_order_ids.read(),
        }
        return self.env.ref(
            'employee_purchase_requisition.action_report_purchase_requisition').report_action(
            self, data=data)


class RequisitionProducts(models.Model):
    _name = 'requisition.order'
    _description = 'Requisition order'

    requisition_product_id = fields.Many2one(
        'employee.purchase.requisition', help='Requisition product.')
    state = fields.Selection(string='State',
                             related='requisition_product_id.state')
    requisition_type = fields.Selection(
        string='Requisition Type',
        selection=[
            ('purchase_order', 'Purchase Order'),
            ('internal_transfer', 'Internal Transfer'),
        ], help='type of requisition')
    product_id = fields.Many2one('product.product', required=True,
                                 help='Product')
    description = fields.Text(
        string="Description",
        compute='_compute_name',
        store=True, readonly=False,
        precompute=True, help='Product Description')
    quantity = fields.Integer(string='Quantity', help='Quantity')
    uom = fields.Char(related='product_id.uom_id.name',
                      string='Unit of Measure', help='Product Uom')
    partner_id = fields.Many2one('res.partner', string='Vendor',
                                 help='Vendor for the requisition')

    @api.depends('product_id')
    def _compute_name(self):
        """compute product description"""
        for option in self:
            if not option.product_id:
                continue
            product_lang = option.product_id.with_context(
                lang=self.requisition_product_id.employee_id.lang)
            option.description = product_lang.get_product_multiline_description_sale()

    @api.onchange('requisition_type')
    def _onchange_product(self):
        """fetching product vendors"""
        vendors_list = []
        for data in self.product_id.seller_ids:
            vendors_list.append(data.partner_id.id)
        return {'domain': {'partner_id': [('id', 'in', vendors_list)]}}
