# -*- coding: utf-8 -*-
###############################################################################
#
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
###############################################################################
from odoo import api, Command, fields, models
from odoo.exceptions import UserError, ValidationError

# Requisition states in which its lines can still be changed (same rule as
# the form view).
EDITABLE_STATES = ('new', 'waiting_department_approval', 'waiting_head_approval')


class PurchaseRequisition(models.Model):
    """Class for adding fields and functions for purchase requisition model."""
    _name = 'employee.purchase.requisition'
    _description = 'Employee Purchase Requisition'
    _inherit = "mail.thread", "mail.activity.mixin"

    name = fields.Char(string="Reference No", readonly=True)
    employee_id = fields.Many2one(comodel_name='hr.employee',                                   required=True, help='Select an employee')
    dept_id = fields.Many2one(comodel_name='hr.department', string='Department',
                              related='employee_id.department_id', store=True,
                              help='Select an department')
    user_id = fields.Many2one(comodel_name='res.users', string='Responsible',
                              required=True,
                              domain=lambda self: [('share', '=', False),
                                                   ('id', '!=', self.env.uid)],
                              help='Select a user who is responsible for requisition')
    requisition_date = fields.Date(                                   default=lambda self: fields.Date.today(),
                                   help='Date of requisition')
    receive_date = fields.Date(string="Received Date", readonly=True,
                               help='Received date')
    requisition_deadline = fields.Date(                                       help="End date of purchase requisition")
    company_id = fields.Many2one(comodel_name='res.company',                                  default=lambda self: self.env.company,
                                 help='Select a company')
    requisition_order_ids = fields.One2many(comodel_name='requisition.order',
                                            inverse_name='requisition_product_id',
                                            required=True)
    confirm_id = fields.Many2one(comodel_name='res.users',
                                 string='Confirmed By',
                                 default=lambda self: self.env.uid,
                                 readonly=True,
                                 help='User who confirmed the requisition.')
    manager_id = fields.Many2one(comodel_name='res.users',
                                 string='Department Manager', readonly=True,
                                 help='Select a department manager')
    requisition_head_id = fields.Many2one(comodel_name='res.users',
                                          string='Approved By', readonly=True,
                                          help='User who approved the requisition.')
    rejected_user_id = fields.Many2one(comodel_name='res.users',
                                       string='Rejected By', readonly=True,
                                       help='User who rejected the requisition')
    confirmed_date = fields.Date(readonly=True,
                                 help='Date of requisition confirmation')
    department_approval_date = fields.Date(                                           readonly=True,
                                           help='Department approval date')
    approval_date = fields.Date(string='Approved Date', readonly=True,
                                help='Requisition approval date')
    reject_date = fields.Date(string='Rejection Date', readonly=True,
                              help='Requisition rejected date')
    source_location_id = fields.Many2one(comodel_name='stock.location',
                                                                                  help='Source location of requisition.', readonly=True)
    destination_location_id = fields.Many2one(comodel_name='stock.location',
                                                                                            help='Destination location of requisition.', readonly=True)
    delivery_type_id = fields.Many2one(comodel_name='stock.picking.type',
                                       string='Delivery To',
                                       help='Type of delivery.', readonly=True)
    internal_picking_id = fields.Many2one(comodel_name='stock.picking.type',
                                          readonly=True)
    requisition_description = fields.Text(string="Reason For Requisition")
    purchase_count = fields.Integer(                                    help='Purchase count',
                                    compute='_compute_purchase_count')
    internal_transfer_count = fields.Integer(string='Internal Transfer count',
                                             help='Internal transfer count',
                                             compute='_compute_internal_transfer_count')
    state = fields.Selection([('new', 'New'), ('waiting_department_approval',
                                               'Waiting Department Approval'),
                              ('waiting_head_approval',
                               'Waiting Head Approval'),
                              ('approved', 'Approved'),
                              ('purchase_order_created',
                               'Purchase Order Created'),
                              ('received', 'Received'),
                              ('cancelled', 'Cancelled')], default='new',
                             copy=False, tracking=True)

    # The counts are shown on the requisition form, which requisition users
    # open without purchase or inventory rights: count elevated (a number only).
    def _compute_internal_transfer_count(self):
        """Function to compute the transfer count"""
        for rec in self:
            if not rec.id or rec.name == 'New':
                rec.internal_transfer_count = 0
            else:
                rec.internal_transfer_count = self.env['stock.picking'].sudo().search_count([
                    ('requisition_order', '=', rec.name)
                ])

    def _compute_purchase_count(self):
        """Function to compute the purchase count"""
        for rec in self:
            if not rec.id or rec.name == 'New':
                rec.purchase_count = 0
            else:
                rec.purchase_count = self.env['purchase.order'].sudo().search_count([
                    ('requisition_order', '=', rec.name)
                ])

    def _linked_purchase_orders(self):
        """Purchase orders created from these requisitions. Read elevated:
        a requisition user may not have purchase rights."""
        return self.env['purchase.order'].sudo().search(
            [('requisition_order', 'in', self.mapped('name'))])

    @api.ondelete(at_uninstall=False)
    def _unlink_except_confirmed_purchase(self):
        """A requisition whose purchase order is confirmed cannot be deleted."""
        if self._linked_purchase_orders().filtered(lambda po: po.state == 'purchase'):
            raise UserError(self.env._(
                "You cannot delete this record as the purchase order is confirmed"))

    def unlink(self):
        """Cancel the purchase orders created from the deleted requisitions,
        once super() has run the confirmed-order check above."""
        orders = self._linked_purchase_orders()
        res = super().unlink()
        orders.write({'state': 'cancel'})
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Function to generate purchase requisition sequence"""
        for vals in vals_list:
            if not self.env.su and vals.get('state', 'new') != 'new':
                raise UserError(self.env._("A new requisition always starts in the New state."))
            name = vals.get('name')
            if not name or name == self.env._('New') or self.search([('name', '=', name)], limit=1):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'employee.purchase.requisition') or self.env._('New')
        return super().create(vals_list)

    def write(self, vals):
        """The state only changes through the workflow buttons."""
        if 'state' in vals and not self.env.su:
            raise UserError(self.env._(
                "The state of a requisition can only be changed with its buttons."))
        return super().write(vals)

    def _check_state(self, *states):
        """Raise unless every requisition is in one of ``states``."""
        for rec in self:
            if rec.state not in states:
                raise UserError(self.env._(
                    "%(name)s is in the state “%(state)s”: this action is not available.",
                    name=rec.name, state=dict(self._fields['state'].selection)[rec.state]))

    def _set_state(self, state):
        """Move to ``state``. Called by the workflow buttons once their own
        checks have passed; the caller must be able to edit the record."""
        self.check_access('write')
        self.sudo().write({'state': state})

    def action_confirm_requisition(self):
        """Function to confirm purchase requisition"""
        self._check_state('new')
        if not self.requisition_order_ids:
            raise UserError(self.env._("Add at least a requisition order before confirming."))
        self.source_location_id = (
            self.employee_id.sudo().department_id.department_location_id.id) if (
            self.employee_id.sudo().department_id.department_location_id) else (
            self.env.ref('stock.stock_location_stock').id)
        self.destination_location_id = (
            self.employee_id.sudo().employee_location_id.id) if (
            self.employee_id.sudo().employee_location_id) else (
            self.env.ref('stock.stock_location_stock').id)
        self.delivery_type_id = (
            self.source_location_id.warehouse_id.in_type_id.id)
        self.internal_picking_id = (
            self.source_location_id.warehouse_id.int_type_id.id)
        self._set_state('waiting_department_approval')
        self.confirm_id = self.env.uid
        self.confirmed_date = fields.Date.today()

    def action_department_approval(self):
        """Approval from department manager"""
        self._check_state('waiting_department_approval')
        if not self.env.user.has_groups('employee_purchase_requisition.employee_requisition_manager,'
                                        '!employee_purchase_requisition.employee_requisition_head'):
            raise UserError(self.env._(
                "Only a Requisition Manager can approve at the Department Approval stage. "
                "A Department Head can only approve at the Head Approval stage."))
        for rec in self.requisition_order_ids:
            if rec.requisition_type == 'purchase_order' and not rec.partner_id:
                raise ValidationError(self.env._('Select a vendor'))
        self._set_state('waiting_head_approval')
        self.manager_id = self.env.uid
        self.department_approval_date = fields.Date.today()

    def action_department_cancel(self):
        """Cancellation from department manager"""
        self._check_state('waiting_department_approval')
        if not self.env.user.has_groups('employee_purchase_requisition.employee_requisition_manager,'
                                        '!employee_purchase_requisition.employee_requisition_head'):
            raise UserError(self.env._(
                "Only a Requisition Manager can reject at the Department Approval stage. "
                "A Department Head can only reject at the Head Approval stage."))
        self._set_state('cancelled')
        self.rejected_user_id = self.env.uid
        self.reject_date = fields.Date.today()

    def _check_head_decision(self):
        """Common checks of the head approval and rejection."""
        self._check_state('waiting_head_approval')
        if not self.env.user.has_group('employee_purchase_requisition.employee_requisition_head'):
            raise UserError(self.env._("Only a Department Head can approve or reject at the Head Approval stage."))
        if self.env.user in self.manager_id:
            raise UserError(self.env._(
                "The user who approved at the Department Approval stage cannot "
                "approve or reject at the Head Approval stage."))

    def action_head_approval(self):
        """Approval from department head"""
        self._check_head_decision()
        self._set_state('approved')
        self.requisition_head_id = self.env.uid
        self.approval_date = fields.Date.today()

    def action_head_cancel(self):
        """Cancellation from department head"""
        self._check_head_decision()
        self._set_state('cancelled')
        self.rejected_user_id = self.env.uid
        self.reject_date = fields.Date.today()

    def action_create_purchase_order(self):
        """Create purchase order and internal transfer"""
        self._check_state('approved')
        if not self.env.user.has_group('employee_purchase_requisition.employee_requisition_manager'):
            raise UserError(self.env._("Only a Requisition Manager can create the picking and the purchase order."))
        PurchaseOrder = self.env['purchase.order']
        vendor_po_map = {}
        for rec in self.requisition_order_ids:
            if rec.requisition_type == 'internal_transfer':
                self.env['stock.picking'].create({
                    'location_id': self.source_location_id.id,
                    'location_dest_id': self.destination_location_id.id,
                    'picking_type_id': self.internal_picking_id.id,
                    'requisition_order': self.name,
                    'move_ids': [Command.create({
                        'product_id': rec.product_id.id,
                        'uom_id': rec.product_id.uom_id.id,
                        'product_uom_qty': rec.quantity,
                        'location_id': self.source_location_id.id,
                        'location_dest_id': self.destination_location_id.id,
                    })]
                })
            else:
                vendor=rec.partner_id.id
                if vendor in vendor_po_map:
                    po = vendor_po_map[vendor]
                else:
                    po = PurchaseOrder.create({
                        'partner_id': vendor,
                        'requisition_order': self.name,
                    })
                    vendor_po_map[vendor] = po
                po.write({
                    "order_line": [Command.create({
                        'product_id': rec.product_id.id,
                        'product_qty': rec.quantity,
                    })]
                })
        self._set_state('purchase_order_created')

    def action_receive(self):
        """Received purchase requisition"""
        self._check_state('purchase_order_created')
        if not self.env.user.has_group('employee_purchase_requisition.employee_requisition_manager'):
            raise UserError(self.env._("Only a Requisition Manager can mark the requisition as received."))
        self._set_state('received')
        self.receive_date = fields.Date.today()

    def get_purchase_order(self):
        """Purchase order smart button view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Purchase Order'),
            'view_mode': 'list,form',
            'res_model': 'purchase.order',
            'domain': [('requisition_order', '=', self.name)],
        }

    def get_internal_transfer(self):
        """Internal transfer smart tab view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Internal Transfers'),
            'view_mode': 'list,form',
            'res_model': 'stock.picking',
            'domain': [('requisition_order', '=', self.name)],
        }

    def action_print_report(self):
        """Print purchase requisition report"""
        return self.env.ref(
            'employee_purchase_requisition.'
            'action_report_purchase_requisition').report_action(self)
