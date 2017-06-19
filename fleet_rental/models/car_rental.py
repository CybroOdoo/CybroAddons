# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Avinash Nk(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime, date
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CarRentalContract(models.Model):
    _name = 'car.rental.contract'

    contract_name = fields.Char(string="Name", default="Draft Contract", readonly=True)
    name = fields.Many2one('res.partner', required=True, help="Customer")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle To Rent", required=True)
    car_brand = fields.Char(string="Car Brand", size=50)
    car_color = fields.Char(string="Car Color", size=50)
    cost = fields.Float(string="Rent Cost", help="This fields is to determine the cost of rent per hour", required=True)
    rent_start_date = fields.Date(string="Rent Start Date", required=True, default=datetime.today())
    rent_end_date = fields.Date(string="Rent End Date", required=True)
    state = fields.Selection([('draft', 'Draft'), ('running', 'Running'), ('cancel', 'Cancel'),
                              ('checking', 'Checking'), ('done', 'Done')], string="State", default="draft")
    notes = fields.Text(string="Details")
    cost_generated = fields.Float('Recurring Cost',
                                  help="Costs paid at regular intervals, depending on the cost frequency")
    cost_frequency = fields.Selection([('no', 'No'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'),
                                       ('yearly', 'Yearly')], string="Recurring Cost Frequency",
                                      help='Frequency of the recurring cost', required=True)
    journal_type = fields.Many2one('account.journal', 'Journal',
                                   default=lambda self: self.env['account.journal'].search([('id', '=', 1)]))
    account_type = fields.Many2one('account.account', 'Account',
                                   default=lambda self: self.env['account.account'].search([('id', '=', 17)]))
    recurring_line = fields.One2many('fleet.rental.line', 'rental_number', readonly=True)
    first_payment = fields.Float(string='First Payment')
    first_invoice_created = fields.Boolean(string="First Invoice Created", invisible=True)
    attachment_ids = fields.Many2many('ir.attachment', 'car_rent_checklist_ir_attachments_rel',
                                      'rental_id', 'attachment_id', string="Attachments",
                                      help="Images of the vehicle before contract/any attachments")
    checklist_line = fields.One2many('car.rental.checklist', 'checklist_number', string="Checklist")
    total = fields.Float(string="Total(Tools)", readonly=True)
    tools_missing_cost = fields.Float(string="Tools missing cost", readonly=True)
    damage_cost = fields.Float(string="Damage cost")
    damage_cost_sub = fields.Float(string="Damage cost", readonly=True)
    total_cost = fields.Float(string="Total cost", readonly=True)

    @api.constrains('state')
    def state_changer(self):
        if self.state == "running":
            state_id = self.env['fleet.vehicle.state'].search([('name', '=', "Rent")]).id
            self.vehicle_id.write({'state_id': state_id})
        elif self.state == "done":
            state_id = self.env['fleet.vehicle.state'].search([('name', '=', "Active")]).id
            self.vehicle_id.write({'state_id': state_id})

    @api.constrains('checklist_line', 'damage_cost')
    def total_updater(self):
        total = 0.0
        tools_missing_cost = 0.0
        for records in self.checklist_line:
            total += records.price
            if not records.checklist_active:
                tools_missing_cost += records.price
        self.total = total
        self.tools_missing_cost = tools_missing_cost
        self.damage_cost_sub = self.damage_cost
        self.total_cost = tools_missing_cost + self.damage_cost

    @api.model
    def fleet_scheduler(self):
        inv_obj = self.env['account.invoice']
        inv_line_obj = self.env['account.invoice.line']
        recurring_obj = self.env['fleet.rental.line']
        today = date.today()
        for records in self.search([]):
            start_date = datetime.strptime(records.rent_start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(records.rent_end_date, '%Y-%m-%d').date()
            if end_date >= date.today():
                temp = 0
                if records.cost_frequency == 'daily':
                    temp = 1
                elif records.cost_frequency == 'weekly':
                    week_days = (date.today() - start_date).days
                    if week_days % 7 == 0 and week_days != 0:
                        temp = 1
                elif records.cost_frequency == 'monthly':
                    if start_date.day == date.today().day and start_date != date.today():
                        temp = 1
                elif records.cost_frequency == 'yearly':
                    if start_date.day == date.today().day and start_date.month == date.today().month and \
                                    start_date != date.today():
                        temp = 1
                if temp == 1 and records.cost_frequency != "no" and records.state == "running":
                    supplier = records.name
                    inv_data = {
                        'name': supplier.name,
                        'reference': supplier.name,
                        'account_id': supplier.property_account_payable_id.id,
                        'partner_id': supplier.id,
                        'currency_id': records.account_type.company_id.currency_id.id,
                        'journal_id': records.journal_type.id,
                        'origin': records.vehicle_id.name,
                        'company_id': records.account_type.company_id.id,
                        'date_due': self.rent_end_date,
                    }
                    inv_id = inv_obj.create(inv_data)
                    product_id = self.env['product.product'].search([("name", "=", "Fleet Rental Service")])
                    if product_id.property_account_income_id.id:
                        income_account = product_id.property_account_income_id
                    elif product_id.categ_id.property_account_income_categ_id.id:
                        income_account = product_id.categ_id.property_account_income_categ_id
                    else:
                        raise UserError(
                            _('Please define income account for this product: "%s" (id:%d).') % (product_id.name,
                                                                                                 product_id.id))
                    recurring_data = {
                        'name': records.vehicle_id.name,
                        'date_today': today,
                        'account_info': income_account.name,
                        'rental_number': records.id,
                        'recurring_amount': records.cost_generated,
                        'invoice_number': inv_id.id
                    }
                    recurring_obj.create(recurring_data)
                    inv_line_data = {
                        'name': records.vehicle_id.name,
                        'account_id': income_account.id,
                        'price_unit': records.cost_generated,
                        'quantity': 1,
                        'product_id': product_id.id,
                        'invoice_id': inv_id.id,
                    }
                    inv_line_obj.create(inv_line_data)
            else:
                records.state = "checking"

    @api.multi
    def action_verify(self):
        self.state = "done"
        if self.total_cost != 0:
            inv_obj = self.env['account.invoice']
            inv_line_obj = self.env['account.invoice.line']
            supplier = self.name
            inv_data = {
                'name': supplier.name,
                'reference': supplier.name,
                'account_id': supplier.property_account_payable_id.id,
                'partner_id': supplier.id,
                'currency_id': self.account_type.company_id.currency_id.id,
                'journal_id': self.journal_type.id,
                'origin': self.vehicle_id.name,
                'company_id': self.account_type.company_id.id,
                'date_due': self.rent_end_date,
            }
            inv_id = inv_obj.create(inv_data)
            product_id = self.env['product.product'].search([("name", "=", "Fleet Rental Service")])
            if product_id.property_account_income_id.id:
                income_account = product_id.property_account_income_id
            elif product_id.categ_id.property_account_income_categ_id.id:
                income_account = product_id.categ_id.property_account_income_categ_id
            else:
                raise UserError(
                    _('Please define income account for this product: "%s" (id:%d).') % (product_id.name,
                                                                                         product_id.id))
            inv_line_data = {
                'name': "Damage/Tools missing cost",
                'account_id': income_account.id,
                'price_unit': self.total_cost,
                'quantity': 1,
                'product_id': product_id.id,
                'invoice_id': inv_id.id,
            }
            inv_line_obj.create(inv_line_data)
            imd = self.env['ir.model.data']
            action = imd.xmlid_to_object('account.action_invoice_tree1')
            list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
            form_view_id = imd.xmlid_to_res_id('account.invoice_form')
            result = {
                'name': action.name,
                'help': action.help,
                'type': 'ir.actions.act_window',
                'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                          [False, 'calendar'], [False, 'pivot']],
                'target': action.target,
                'context': action.context,
                'res_model': 'account.invoice',
            }
            if len(inv_id) > 1:
                result['domain'] = "[('id','in',%s)]" % inv_id.ids
            elif len(inv_id) == 1:
                result['views'] = [(form_view_id, 'form')]
                result['res_id'] = inv_id.ids[0]
            else:
                result = {'type': 'ir.actions.act_window_close'}
            return result

    @api.multi
    def action_confirm(self):
        self.state = "running"
        sequence_code = 'car.rental.sequence'
        order_date = self.create_date
        order_date = order_date[0:10]
        self.contract_name = self.env['ir.sequence']\
            .with_context(ir_sequence_date=order_date).next_by_code(sequence_code)

    @api.multi
    def action_cancel(self):
        self.state = "cancel"

    @api.multi
    def force_checking(self):
        self.state = "checking"

    @api.multi
    def action_invoice_create(self):
        self.first_invoice_created = True
        inv_obj = self.env['account.invoice']
        inv_line_obj = self.env['account.invoice.line']
        supplier = self.name
        inv_data = {
            'name': supplier.name,
            'reference': supplier.name,
            'account_id': supplier.property_account_payable_id.id,
            'partner_id': supplier.id,
            'currency_id': self.account_type.company_id.currency_id.id,
            'journal_id': self.journal_type.id,
            'origin': self.vehicle_id.name,
            'company_id': self.account_type.company_id.id,
            'date_due': self.rent_end_date,
        }
        inv_id = inv_obj.create(inv_data)
        product_id = self.env['product.product'].search([("name", "=", "Fleet Rental Service")])
        if product_id.property_account_income_id.id:
            income_account = product_id.property_account_income_id.id
        elif product_id.categ_id.property_account_income_categ_id.id:
            income_account = product_id.categ_id.property_account_income_categ_id.id
        else:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d).') % (product_id.name,
                                                                                     product_id.id))
        inv_line_data = {
            'name': self.vehicle_id.name,
            'account_id': income_account,
            'price_unit': self.first_payment,
            'quantity': 1,
            'product_id': product_id.id,
            'invoice_id': inv_id.id,
        }
        inv_line_obj.create(inv_line_data)
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree1')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': 'ir.actions.act_window',
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': 'account.invoice',
        }
        if len(inv_id) > 1:
            result['domain'] = "[('id','in',%s)]" % inv_id.ids
        elif len(inv_id) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = inv_id.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.onchange('vehicle_id')
    def update_fields(self):
        if self.vehicle_id:
            obj = self.env['fleet.vehicle'].search([('name', '=', self.vehicle_id.name)])
            self.car_brand = obj.model_id.brand_id.name
            self.car_color = obj.color


class FleetRentalLine(models.Model):
    _name = 'fleet.rental.line'

    name = fields.Char('Description')
    date_today = fields.Date('Date')
    account_info = fields.Char('Account')
    recurring_amount = fields.Float('Amount')
    rental_number = fields.Integer('Rental Number')
    payment_info = fields.Char(string='Payment Stage', compute='paid_info')
    invoice_number = fields.Integer(string='Invoice ID')

    @api.one
    def paid_info(self):
        if self.env['account.invoice'].browse(self.invoice_number):
            self.payment_info = self.env['account.invoice'].browse(self.invoice_number).state
        else:
            self.payment_info = 'Record Deleted'


class CarRentalChecklist(models.Model):
    _name = 'car.rental.checklist'

    name = fields.Many2one('car.tools', string="Name")
    checklist_active = fields.Boolean(string="Active", default=True)
    checklist_number = fields.Many2one('car.rental.contract', string="Checklist number")
    price = fields.Float(string="Price")

    @api.onchange('name')
    def onchange_name(self):
        self.price = self.name.price


class CarTools(models.Model):
    _name = 'car.tools'

    name = fields.Char(string="Name")
    price = fields.Float(string="Price")
