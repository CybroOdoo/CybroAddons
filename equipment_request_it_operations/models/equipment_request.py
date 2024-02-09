# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models
from odoo.exceptions import UserError


class EquipmentRequest(models.Model):
    """ Model representing equipment request records.
    This model stores information about equipment requests made by employees,
    including details such as the type of request (software or hardware), the
    employee making the request, the department, job position, user who created
    the request, and other related information.
    The model also includes fields to track the approval status of the request,
    any damages associated with the equipment, expenses related to the request,
    and internal orders associated with the request."""

    _name = "equipment.request"
    _description = "Model representing equipment requests made by employees"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(compute='_compute_name',
                       help="Auto-generated field based on record's ID")
    request_for = fields.Selection([
        ('software', 'Software'),
        ('hardware', 'Hardware')], string='Request For',
        copy=False, default='software', required=True,
        help="Type of Equipment Request")
    employee_name_id = fields.Many2one('hr.employee', string='Employee',
                                       required=True,
                                       help="Employee requesting the equipment")
    department_name_id = fields.Many2one('hr.department', string='Department',
                                         help="Department of the employee")
    job_position_id = fields.Many2one('hr.job', string='Job Position',
                                      help="Job position of the employee")
    user_login_id = fields.Many2one('res.users', string='User',
                                    default=lambda self: self.env.user,
                                    help="User who created the equipment "
                                         "request")
    damage_check = fields.Boolean(string='Damage',
                                  help="Whether the equipment"
                                       " is damaged or not", tracking=True)
    company_name_id = fields.Many2one('res.company', string='Company',
                                      default=lambda self: self.env.company,
                                      help="Company of the employee")
    source_location_id = fields.Many2one('stock.location',
                                         string='Source Location',
                                         help="Location from where the "
                                              "equipment"
                                              "will be sourced")
    destination_location_id = fields.Many2one('stock.location',
                                              string='Destination Location',
                                              help="Location where the "
                                                   "equipment"
                                                   "will be sent")
    created_user_id = fields.Many2one('res.users', string='Created By',
                                      default=lambda self: self.env.user,
                                      help="User who created the equipment "
                                           "request")
    create_date = fields.Date(string='Created Date',
                              help="Date when the equipment "
                                   "request was created", tracking=True)
    validate_user_id = fields.Many2one('res.users', string='Department Manager',
                                       help="Manager who approves the equipment"
                                            "request")
    validate_date = fields.Date(string='Department Approved Date',
                                help="Date when the department manager approved"
                                     "the equipment request")
    hr_user_id = fields.Many2one('res.users', string='HR Manager',
                                 help="HR Manager who approves the equipment "
                                      "request")
    hr_date = fields.Date(string='HR Approved Date',
                          help="Date when the HR Manager approved the equipment"
                               "request")
    stock_user_id = fields.Many2one('res.users', string='Stock Manager',
                                    help="Stock Manager who approves the "
                                         "equipment"
                                         "request")
    stock_date = fields.Date(string='Stock Approved Date',
                             help="Date when the Stock Manager approved the "
                                  "equipment request")
    status = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting for Approval of Department'),
        ('approval', 'Waiting For Approval of HR'),
        ('approved', 'Approved'),
        ('assigned', 'Equipment Assigned'),
        ('reject', 'Rejected')],
        string='State', copy=False, default='draft',
        help="Status of the equipment request", tracking=True)
    is_expensed = fields.Boolean(default=False,
                                 help="Whether the equipment request has been "
                                      "expensed or not")
    equipment_request_ids = fields.One2many('equipment.detail',
                                            'equipment_detail_id',
                                            string='Request Equipments',
                                            help="Equipment details for the "
                                                 "equipment request")
    equipment_damage_ids = fields.One2many('damage.detail',
                                           'equipment_damage_id',
                                           string='Damage Details',
                                           help="Details of damages (if any) "
                                                "for"
                                                "the equipment")
    equipment_expense_ids = fields.One2many('hr.expense',
                                            'equipment_expense_id',
                                            string='Expenses',
                                            help="Expenses (if any) associated "
                                                 "with the equipment request")
    equipment_internal_ids = fields.One2many('stock.picking',
                                             'equipment_transfer_id',
                                             string='Internal Orders',
                                             help="The internal orders "
                                                  "related to"
                                                  "this equipment request.")

    @api.onchange('employee_name_id')
    def _onchange_employee_name_id(self):
        """Changing the Employee will also write the Department he belongs to
        and also Job Position"""
        if self.employee_name_id:
            self.department_name_id = self.employee_name_id.department_id
            self.job_position_id = self.employee_name_id.job_id

    @api.depends('request_for', 'employee_name_id')
    def _compute_name(self):
        """ _rec_name = Employee Name + Request Type + Creation Date"""
        for record in self:
            record.name = str(record.employee_name_id.name) + ' - ' + str(
                record.request_for) + ' - ' + str(
                fields.date.today())

    def action_confirm(self):
        """Confirm Button"""
        self.write({'status': 'waiting'})

    def action_reject(self):
        """Reject Button"""
        self.write({'status': 'reject'})

    def action_waiting_approval_dept(self):
        """Department Approval Button also write the user who Approved this
        button and Date he approved"""
        self.write({'status': 'approval', 'validate_user_id': self.env.user.id,
                    'validate_date': fields.Date.today()})

    def action_waiting_approval_hr(self):
        """HR Approval Button also write the user who Approved this button
        and Date he approved"""
        self.write({'status': 'approved', 'hr_user_id': self.env.user.id,
                    'hr_date': fields.Date.today()})

    def action_internal_transfer(self):
        """Create Internal Transfer and Go the Final Status if no source
        location and destination location User Error Shows"""
        if not self.source_location_id:
            raise UserError('Source Location is not defined')
        if not self.destination_location_id:
            raise UserError('Destination Location is not defined')
        picking_type_id = self.env['stock.picking.type'].search(
            [('code', '=', 'internal')])
        if not picking_type_id:
            picking_type_id = self.env['stock.picking.type'].create({
                'name': 'Internal Transfers',
                'code': 'internal',
                'sequence_code': 'INT',
            })
        move_vals = {
            'picking_type_id': picking_type_id.id,
            'location_id': self.source_location_id.id,
            'location_dest_id': self.destination_location_id.id,
            'equipment_transfer_id': self.id,
        }
        picking = self.env['stock.picking'].create(move_vals)
        for value in self.equipment_request_ids:
            self.env['stock.move'].create({
                'picking_id': picking.id,
                'name': value.product_id.name,
                'product_id': value.product_id.id,
                'product_uom_qty': value.quantity,
                'product_uom': value.product_id.uom_id.id,
                'location_id': self.source_location_id.id,
                'location_dest_id': self.destination_location_id.id,
            })
        picking.action_confirm()
        picking.action_assign()
        self.write({'status': 'assigned', 'stock_user_id': self.env.user.id,
                    'stock_date': fields.Date.today()})

    def action_expense(self):
        """Button of Create Expense And will Create Expense in Expense Module"""
        if self.equipment_damage_ids:
            for value in self.equipment_damage_ids:
                self.env['hr.expense'].create({
                    'total_amount': value.unit_price,
                    'name': self.name,
                    'employee_id': self.employee_name_id.id,
                    'product_id': value.product_id.id,
                    'equipment_expense_id': self.id,
                })
            self.is_expensed = True

    def action_smart_expense(self):
        """View the Expense in the Smart Tab and also can Approve it from the
        Smart Tab"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Expense',
            'res_model': 'hr.expense',
            'target': 'current',
            'domain': [('name', '=', self.name),
                       ('employee_id', '=', self.employee_name_id.id),
                       ('equipment_expense_id', '=', self.id)],
            'view_mode': 'tree,form',
        }

    def action_view_internal_transfer(self):
        """View Current Record of the Internal Transfer Button"""
        picking_id = self.env['stock.picking'].search([
            ('picking_type_id.code', '=', 'internal'),
            ('location_id', '=', self.source_location_id.id),
            ('location_dest_id', '=', self.destination_location_id.id),
        ], limit=1, order='create_date desc')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Internal Transfer',
            'view_mode': 'form',
            'target': 'current',
            'res_model': 'stock.picking',
            'res_id': picking_id.id
        }
