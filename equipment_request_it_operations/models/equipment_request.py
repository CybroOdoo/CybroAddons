# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arshad Ali Pottengal (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models
from odoo.exceptions import UserError

GROUP_PREFIX = ('equipment_request_it_operations.'
                'equipment_request_it_operations_group_')


class EquipmentRequest(models.Model):
    """ Model representing equipment request records.
    This model stores information about equipment requests made by
    employees, including the type of request (software or hardware), the
    employee making the request, the department, the job position, the user
    who created the request and other related information.
    The model also tracks the approval status of the request, any damages
    associated with the equipment, the related expenses and the internal
    orders of the request. """
    _name = "equipment.request"
    _description = "Model representing equipment requests made by employees"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(compute='_compute_name', store=True,
                       help="Employee name, request type and creation date")
    request_for = fields.Selection([
        ('software', 'Software'),
        ('hardware', 'Hardware')],
        copy=False, default='software', required=True,
        help="Type of equipment request")
    employee_name_id = fields.Many2one(
        'hr.employee', string='Employee', required=True,
        help="Employee requesting the equipment")
    department_name_id = fields.Many2one(
        'hr.department', string='Department',
        help="Department of the employee")
    job_position_id = fields.Many2one(
        'hr.job', help="Job position of the employee")
    user_login_id = fields.Many2one(
        'res.users', string='User', default=lambda self: self.env.user,
        help="User who created the equipment request")
    damage_check = fields.Boolean(
        string='Damage', tracking=True,
        help="Whether the equipment is damaged or not")
    company_name_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
        help="Company of the employee")
    source_location_id = fields.Many2one(
        'stock.location',
        help="Location from where the equipment will be sourced")
    destination_location_id = fields.Many2one(
        'stock.location', help="Location where the equipment will be sent")
    created_user_id = fields.Many2one(
        'res.users', string='Created By',
        default=lambda self: self.env.user,
        help="User who created the equipment request")
    request_create_date = fields.Date(
        string='Created Date', default=fields.Date.context_today,
        tracking=True, help="Date when the equipment request was created")
    validate_user_id = fields.Many2one(
        'res.users', string='Department Manager',
        help="Manager who approves the equipment request")
    validate_date = fields.Date(
        string='Department Approved Date',
        help="Date when the department manager approved the equipment "
             "request")
    hr_user_id = fields.Many2one(
        'res.users', string='HR Manager',
        help="HR Manager who approves the equipment request")
    hr_date = fields.Date(
        string='HR Approved Date',
        help="Date when the HR Manager approved the equipment request")
    stock_user_id = fields.Many2one(
        'res.users', string='Stock Manager',
        help="Stock Manager who approves the equipment request")
    stock_date = fields.Date(
        string='Stock Approved Date',
        help="Date when the Stock Manager approved the equipment request")
    status = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting for Approval of Department'),
        ('approval', 'Waiting for Approval of HR'),
        ('approved', 'Approved'),
        ('assigned', 'Equipment Assigned'),
        ('reject', 'Rejected')],
        string='State', copy=False, default='draft', tracking=True,
        help="Status of the equipment request")
    is_expensed = fields.Boolean(
        default=False,
        help="Whether the expenses of the equipment request were generated")
    equipment_request_ids = fields.One2many(
        'equipment.detail', 'equipment_detail_id',
        string='Request Equipment',
        help="Equipment details for the equipment request")
    equipment_damage_ids = fields.One2many(
        'damage.detail', 'equipment_damage_id', string='Damage Details',
        help="Details of damages (if any) for the equipment")
    equipment_expense_ids = fields.One2many(
        'hr.expense', 'equipment_expense_id', string='Expenses',
        help="Expenses (if any) associated with the equipment request")
    equipment_internal_ids = fields.One2many(
        'stock.picking', 'equipment_transfer_id', string='Internal Orders',
        help="The internal orders related to this equipment request")

    @api.onchange('employee_name_id')
    def _onchange_employee_name_id(self):
        """ Changing the employee also fills in their department and job
        position. """
        if self.employee_name_id:
            self.department_name_id = self.employee_name_id.department_id
            self.job_position_id = self.employee_name_id.job_id

    @api.depends('request_for', 'employee_name_id', 'create_date')
    def _compute_name(self):
        """ Name = employee name + request type + creation date """
        for record in self:
            creation_date = (
                fields.Datetime.context_timestamp(
                    record, record.create_date).date()
                if record.create_date
                else fields.Date.context_today(record)
            )
            record.name = (
                f"{record.employee_name_id.name or ''} - "
                f"{record.request_for or ''} - "
                f"{creation_date}"
            )

    def _has_equipment_group(self, *groups):
        """ Return True if the current user belongs to any of the given
        equipment groups (department_manager, hr_officer, stock_manager). """
        return any(self.env.user.has_group(GROUP_PREFIX + group)
                   for group in groups)

    def action_confirm(self):
        """ Confirm the request and send it for department approval """
        for record in self:
            if record.status != 'draft':
                raise UserError(self.env._(
                    "Only draft equipment requests can be confirmed."))
            record.write({'status': 'waiting'})

    def action_reject(self):
        """ Reject the request """
        if not self._has_equipment_group(
                'department_manager', 'hr_officer', 'stock_manager'):
            raise UserError(self.env._(
                "You do not have permission to reject this request."))
        for record in self:
            if record.status == 'reject':
                raise UserError(self.env._("Request is already rejected."))
            record.write({'status': 'reject'})

    def action_waiting_approval_dept(self):
        """ Department approval; records the approving user and the
        approval date. """
        if not self._has_equipment_group('department_manager'):
            raise UserError(self.env._(
                "Only Department Managers can approve this request."))
        for record in self:
            if record.status != 'waiting':
                raise UserError(self.env._(
                    "Only requests waiting for department approval can be "
                    "approved."))
            record.write({'status': 'approval',
                          'validate_user_id': self.env.user.id,
                          'validate_date': fields.Date.today()})

    def action_waiting_approval_hr(self):
        """ HR approval; records the approving user and the approval
        date. """
        if not self._has_equipment_group('hr_officer'):
            raise UserError(self.env._(
                "Only HR Officers can approve this request."))
        for record in self:
            if record.status != 'approval':
                raise UserError(self.env._(
                    "Only requests waiting for HR approval can be "
                    "approved."))
            record.write({'status': 'approved',
                          'hr_user_id': self.env.user.id,
                          'hr_date': fields.Date.today()})

    def action_internal_transfer(self):
        """ Create an internal transfer for the requested equipment and move
        the request to the final status. Raises a UserError when the source
        or destination location is missing. """
        if not self._has_equipment_group('stock_manager'):
            raise UserError(self.env._(
                "Only Stock Managers can create internal transfers."))
        for record in self:
            if record.status != 'approved':
                raise UserError(self.env._(
                    "Internal transfers can only be created for approved "
                    "requests."))
            if not record.source_location_id:
                raise UserError(self.env._('Source Location is not defined'))
            if not record.destination_location_id:
                raise UserError(self.env._(
                    'Destination Location is not defined'))
            # The warehouse internal operation type is archived unless
            # multi-locations is enabled, so include archived types.
            picking_type = self.env['stock.picking.type'].with_context(
                active_test=False).search([
                    ('code', '=', 'internal'),
                    ('company_id', '=', record.company_name_id.id),
                ], limit=1)
            if not picking_type:
                raise UserError(self.env._(
                    "No internal transfer operation type is configured "
                    "for the company %s.", record.company_name_id.name))
            source = record.source_location_id
            destination = record.destination_location_id
            picking = self.env['stock.picking'].create({
                'picking_type_id': picking_type.id,
                'location_id': source.id,
                'location_dest_id': destination.id,
                'equipment_transfer_id': record.id,
                'move_ids': [fields.Command.create({
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': (line.product_uom_id
                                    or line.product_id.uom_id).id,
                    'location_id': source.id,
                    'location_dest_id': destination.id,
                }) for line in record.equipment_request_ids],
            })
            picking.action_confirm()
            picking.action_assign()
            record.write({'status': 'assigned',
                          'stock_user_id': self.env.user.id,
                          'stock_date': fields.Date.today()})

    def action_expense(self):
        """ Create one expense per damage line in the Expense module """
        if not self._has_equipment_group('department_manager'):
            raise UserError(self.env._(
                "Only Department Managers can generate expenses."))
        for record in self:
            if record.status != 'waiting':
                raise UserError(self.env._(
                    "Expenses can only be generated for requests waiting "
                    "for department approval."))
            if record.equipment_damage_ids:
                # Expense record rules only let users create their own
                # expenses; the Department Manager check above authorises
                # creating them on behalf of the requesting employee.
                self.env['hr.expense'].sudo().create([{
                    'name': record.name,
                    'employee_id': record.employee_name_id.id,
                    'product_id': damage.product_id.id,
                    'quantity': damage.quantity,
                    'total_amount_currency': damage.subtotal,
                    'equipment_expense_id': record.id,
                } for damage in record.equipment_damage_ids])
                record.is_expensed = True

    def action_smart_expense(self):
        """ Open the expenses linked to this request from the smart
        button. """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Expenses'),
            'res_model': 'hr.expense',
            'target': 'current',
            'domain': [('name', '=', self.name),
                       ('employee_id', '=', self.employee_name_id.id),
                       ('equipment_expense_id', '=', self.id)],
            'view_mode': 'list,form',
        }

    def action_view_internal_transfer(self):
        """ Open the latest internal transfer of this request """
        self.ensure_one()
        picking = self.env['stock.picking'].search([
            ('equipment_transfer_id', '=', self.id),
        ], limit=1, order='create_date desc')
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Internal Transfer'),
            'view_mode': 'form',
            'target': 'current',
            'res_model': 'stock.picking',
            'res_id': picking.id,
        }
