# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Ayana KP (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo import models, api, fields, _, SUPERUSER_ID


class CarWorkshop(models.Model):
    """ Model for car workshop management """
    _name = 'car.workshop'
    _description = "Car Workshop"
    _inherit = ['mail.thread']

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """ Read group customization in order to display all the stages in the
            kanban view, even if they are empty """
        stage_ids = stages._search([], order=order,
                                   access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    def _default_stage_id(self):
        # Since project stages are order by sequence first,
        # this should fetch the one with the lowest sequence number.
        return self.env['worksheet.stages'].search([], limit=1)

    vehicle_id = fields.Many2one('vehicle.details', string='Vehicle',
                                 index=True, tracking=True, change_default=True,
                                 help='The vehicle for the work started')
    name = fields.Char(string='Title', tracking=True, required=True,
                       help='Give Name of the work')
    user_id = fields.Many2one('res.users', string='Assigned to',
                              default=lambda self: self.env.user, tracking=True,
                              help='Give Name of the user')
    active = fields.Boolean(string='Active', default=True,
                            help='Work is active?')
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 related='vehicle_id.partner_id',
                                 help='Customer or car owner')
    priority = fields.Selection([('0', 'Normal'), ('1', 'High')],
                                string='Priority', index=True, default='0',
                                help='Priority of work')
    description = fields.Html(string='Description',
                              help='Give any notes for the work')
    sequence = fields.Integer(string='Sequence', index=True, default=10,
                              help="Gives the sequence order when displaying "
                                   "a list of tasks.")
    tag_ids = fields.Many2many('worksheet.tag', string='Tags',
                               ondelete='cascade',
                               help='Give tags for the work')
    kanban_state = fields.Selection(
        [('normal', 'In Progress'), ('done', 'Ready for next stage'),
         ('blocked', 'Blocked')], string='Kanban State',
        help="A task's kanban state indicates special situations affecting "
             "it:\n * Normal is the default situation\n"
             "* Blocked indicates something is preventing the progress of "
             "this task\n* Ready for next stage indicates the task is ready "
             "to be pulled to the next stage",
        required=True, tracking=True, default='normal',
        copy=False)
    date_start = fields.Datetime(string='Starting Date',
                                 default=fields.datetime.now(), index=True,
                                 copy=False, help='Give start date of the work')
    date_end = fields.Datetime(string='Ending Date', index=True, copy=False,
                               help='End date of the work')
    date_assign = fields.Date(string='Assigning Date', index=True,
                              default=lambda self: fields.Date.today(),
                              copy=False, help='Date assigned of the work')
    date_deadline = fields.Datetime(string='Deadline', index=True, copy=False,
                                    help='Deadline of the work')
    progress = fields.Integer(string="Working Time Progress(%)", copy=False,
                              readonly=True, help='Work progress details')
    date_last_stage_update = fields.Datetime(string='Last Stage Update',
                                             index=True,
                                             default=fields.datetime.now(),
                                             copy=False, readonly=True,
                                             help='The last stage changed date')
    company_id = fields.Many2one('res.company', string='Company', help='',
                                 required=True,
                                 default=lambda self: self.env.company)
    color = fields.Integer(string='Color Index', help='Choose the color')
    stage_id = fields.Many2one('worksheet.stages', string='Stage',
                               ondelete='restrict', tracking=True, index=True,
                               default=_default_stage_id,
                               group_expand='_read_group_stage_ids',
                               copy=False, help='The stages of the work')
    state = fields.Selection([
        ('waiting', 'Ready'),
        ('workshop_create_invoices', 'Invoiced'),
        ('cancel', 'Invoice Canceled'),
    ], string='Status', readonly=True, default='waiting',
        tracking=True, index=True, help='State of the work')
    attachment_ids = fields.One2many('ir.attachment', 'res_id',
                                     string='Attachments', auto_join=True,
                                     domain=lambda self: [
                                         ('res_model', '=', self._name)],
                                     help='Attachment details of work')
    displayed_image_id = fields.Many2one('ir.attachment',
                                         domain="["
                                                "('res_model', '=', 'car.workshop'),"
                                                "('res_id', '=', id),"
                                                "('mimetype', 'ilike', 'image')]",
                                         string='Displayed Image',
                                         help='Image of the vehicle')
    planned_work_ids = fields.One2many('planned.work', 'work_id',
                                       string='Planned/Ordered Works',
                                       help='The planned work for the vehicle')
    works_done_ids = fields.One2many('planned.work', 'work_id',
                                     string='Work Done',
                                     domain=[('is_completed', '=', True)],
                                     help='The completed work for the vehicle')
    materials_ids = fields.One2many('material.used',
                                    'material_id',
                                    string='Materials Used',
                                    help='Material used for the work')
    remaining_hour = fields.Float(string='Remaining Hour', readonly=True,
                                  compute="_compute_remaining_hour",
                                  help='Remaining hours for the work')
    effective_hour = fields.Float(string='Hours Spent', readonly=True,
                                  compute="_compute_effective_hour",
                                  help='The net working hours for the work ')
    amount_total = fields.Float(string='Total Amount', readonly=True,
                                compute="_compute_amount_total",
                                help='Total amount for the work')
    invoice_count = fields.Integer(string="Invoice_count",
                                   compute='_compute_invoice_count',
                                   help='The invoice count for the work')

    @api.depends('planned_work_ids.work_cost', 'materials_ids.price')
    def _compute_amount_total(self):
        """ Calculate the total amount for each record by summing 'work_cost'
        from 'planned_work_ids' and 'price' from 'materials_ids'. """
        for records in self:
            amount_total = 0.0
            for line in records.planned_work_ids:
                amount_total += line.work_cost
            for line2 in records.materials_ids:
                amount_total += line2.price
            records.amount_total = amount_total

    def cancel(self):
        """ Function for cancel button """
        self.state = 'cancel'

    def action_create_invoices(self):
        """ Function for creating invoice """
        self.state = 'workshop_create_invoices'
        inv_obj = self.env['account.move']
        customer = self.partner_id
        if not customer.name:
            raise UserError(
                _('Please select a Customer.'))
        if not self.planned_work_ids:
            raise UserError(
                _('Nothing to invoice, Plan a work.'))
        invoice_line_ids = []
        self.ensure_one()
        journal_id = self.env['ir.config_parameter'].sudo().get_param(
            'fleet_car_workshop.invoice_journal_type')
        if not journal_id:
            journal_id = self.env['account.journal'].search([
                *self.env['account.journal']._check_company_domain(
                    self.env.company), ('type', '=', 'sale'), ], limit=1)
        inv_data = {
            'ref': self.name,
            'partner_bank_id': customer.bank_ids[:1].id,
            'partner_id': customer.id,
            'currency_id': self.company_id.currency_id.id,
            'journal_id': int(journal_id),
            'invoice_origin': self.name,
            'company_id': self.company_id.id,
            'move_type': 'out_invoice',
        }
        # Get the planned work
        for records in self.planned_work_ids:
            if records.planned_work_id.id:
                income_account = records.planned_work_id.property_account_income_id.id
                if not income_account:
                    raise UserError(
                        _('There is no income account defined for'
                          ' this product: "%s".') %
                        (records.planned_work_id.name,))
                if records.is_completed:
                    inv_line_data = (0, 0, {
                        'name': records.planned_work_id.name,
                        'account_id': income_account,
                        'price_unit': records.work_cost,
                        'quantity': 1,
                        'product_id': records.planned_work_id.id,
                    })
                    invoice_line_ids.append(inv_line_data)
        for records in self.materials_ids:
            if records.material_product_id.id:
                income_account = records.material_product_id.property_account_income_id.id
                if not income_account:
                    raise UserError(
                        _('There is no income account defined '
                          'for this product: "%s".') %
                        (records.material_product_id.name,))
                inv_line_data = (0, 0, {
                    'name': records.material_product_id.name,
                    'account_id': records.material_product_id.property_account_income_id.id,
                    'price_unit': records.price,
                    'quantity': records.quantity,
                    'product_id': records.material_product_id.id,
                })
                invoice_line_ids.append(inv_line_data)
        inv_data.update({
            'invoice_line_ids': invoice_line_ids
        })
        inv_id = inv_obj.create(inv_data)
        result = {
            'type': 'ir.actions.act_window',
            'name': _('Invoice'),
            'view_mode': 'form',
            'res_model': 'account.move',
            'target': 'current',
            'res_id': inv_id.id,
        }
        IMD = self.env['ir.model.data']
        form_view_id = IMD._xmlid_to_res_id('account.invoice_form')
        if len(inv_id) > 1:
            result['domain'] = "[('id','in',%s)]" % inv_id.ids
        elif len(inv_id) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = inv_id.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        invoiced_records = self.env['car.workshop']
        total = 0
        for rows in invoiced_records:
            invoiced_date = rows.date
            invoiced_date = invoiced_date[0:10]
            if invoiced_date == str(date.today()):
                total = total + rows.price_subtotal
        for lines in self.materials_ids:
            product_ids = self.env['product.product'].search(
                [('id', '=', lines.material_product_id.id)])
            for prod_id in product_ids:
                move_id = self.env['stock.picking']
                type_object = self.env['stock.picking.type']
                company_id = self.env.context.get(
                    'company_id') or self.env.user.company_id.id
                types = type_object.search([('code', '=', 'outgoing'), (
                    'warehouse_id.company_id', '=', company_id)],
                                           limit=1)
                vals = {
                    'partner_id': self.partner_id.id,
                    'origin': self.name,
                    'move_type': 'one',
                    'picking_type_id': types.id,
                    'location_id': types.default_location_src_id.id,
                    'location_dest_id': self.partner_id.property_stock_customer.id,
                    'move_ids': [(0, 0, {
                        'name': self.name,
                        'product_id': prod_id.id,
                        'product_uom': prod_id.uom_id.id,
                        'product_uom_qty': lines.quantity,
                        'location_id': types.default_location_src_id.id,
                        'location_dest_id': self.partner_id.property_stock_customer.id,
                    })],
                }
                move = move_id.create(vals)
                move.action_confirm()
                move.action_assign()
                move._action_done()
        return result

    @api.depends('works_done_ids.duration')
    def _compute_effective_hour(self):
        """Function for get total hours spent"""
        for hour in self:
            effective_hour = 0.0
            for line in hour.works_done_ids:
                effective_hour += line.duration
            self.effective_hour = effective_hour

    @api.depends('planned_work_ids.time_spent')
    def _compute_remaining_hour(self):
        """ Function for calculate remaining hours """
        for hour in self:
            remaining_hour = 0.0
            for line in hour.planned_work_ids:
                remaining_hour += line.time_spent
            self.remaining_hour = remaining_hour - self.effective_hour

    def process_demo_scheduler_queue(self):
        # Schedule action function for get work progress
        records = self.search([])
        now = fields.Datetime.from_string(fields.Datetime.now())
        for data in records:
            if data.stage_id.name != 'Done' and data.stage_id.name != 'Cancelled' and data.stage_id.name != 'Verified':
                end_date = fields.Datetime.from_string(data.date_deadline)
                start_date = fields.Datetime.from_string(data.date_assign)
                if data.date_deadline and data.date_assign and end_date > start_date:
                    if now < end_date:
                        diff1 = relativedelta(end_date, start_date)
                        if diff1.days == 0:
                            total_hr = int(diff1.minutes)
                        else:
                            total_hr = int(diff1.days) * 24 * 60 + int(
                                diff1.minutes)
                        diff2 = relativedelta(now, start_date)
                        if diff2.days == 0:
                            current_hr = int(diff2.minutes)
                        else:
                            current_hr = int(diff2.days) * 24 * 60 + int(
                                diff2.minutes)
                        if total_hr != 0:
                            vall = ((current_hr * 100) / total_hr)
                            data.progress = vall
                        else:
                            data.progress = 100
                    else:
                        data.progress = 100
                else:
                    data.progress = 0

    def write(self, vals):
        """ Function for update values in records """
        now = fields.Datetime.now(self)
        # stage change: update date_last_stage_update
        if 'stage_id' in vals:
            vals.update(self._change_date_end(vals['stage_id']))
            vals['date_last_stage_update'] = now
            # reset kanban state when changing stage
            if 'kanban_state' not in vals:
                vals['kanban_state'] = 'normal'
        # user_id change: update date_assign
        if vals.get('user_id') and 'date_assign' not in vals:
            vals['date_assign'] = now
        result = super(CarWorkshop, self).write(vals)
        return result

    def _change_date_end(self, stage_id):
        """ Function for getting last time of stage id changed """
        worksheet_stage = self.env['worksheet.stages'].browse(stage_id)
        if worksheet_stage.is_fold:
            return {'date_end': fields.Datetime.now()}
        return {'date_end': False}

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        # get partner id in the vehicle
        if self.vehicle_id.exists():
            self.partner_id = self.vehicle_id.partner_id

    def action_get_invoices(self):
        """ Function for invoice smart tab """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'account.move',
            'domain': [('invoice_origin', '=', self.name)],
            'context': "{'create': False}"
        }

    def _compute_invoice_count(self):
        """ Function for get total invoice count  """
        for record in self:
            record.invoice_count = self.env['account.move'].search_count(
                [('invoice_origin', '=', self.name)])
