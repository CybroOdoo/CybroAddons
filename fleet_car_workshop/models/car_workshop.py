# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nilmar Shereef(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo import models, api, fields, _


class CarWorkshop(models.Model):
    _name = 'car.workshop'
    _description = "Car Workshop"
    _inherit = ['mail.thread']

    def _get_default_partner(self):
        if 'default_vehicle_id' in self.env.context:
            default_vehicle_id = self.env['car.car'].browse(self.env.context['default_vehicle_id'])
            return default_vehicle_id.exists().partner_id

    name = fields.Char(string='Title', track_visibility='onchange', required=True)
    vehicle_id = fields.Many2one('car.car', string='Vehicle',
                                 default=lambda self: self.env.context.get('default_vehicle_id'), track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='Assigned to', select=True, default=lambda self: self.env.uid)
    active = fields.Boolean(string='Active', default=True)
    partner_id = fields.Many2one('res.partner', string='Customer',default=_get_default_partner)
    priority = fields.Selection([('0', 'Normal'), ('1', 'High')], 'Priority', select=True, default='0')
    description = fields.Html(string='Description')
    sequence = fields.Integer(string='Sequence', select=True,default=10, help="Gives the sequence order when displaying a list of tasks.")
    tag_ids = fields.Many2many('worksheet.tags', string='Tags')
    kanban_state = fields.Selection(
        [('normal', 'In Progress'), ('done', 'Ready for next stage'), ('blocked', 'Blocked')], 'Kanban State',
        help="A task's kanban state indicates special situations affecting it:\n"
             " * Normal is the default situation\n"
             " * Blocked indicates something is preventing the progress of this task\n"
             " * Ready for next stage indicates the task is ready to be pulled to the next stage",
        required=True, track_visibility='onchange',default='normal', copy=False)
    create_date = fields.Datetime(string='Create Date', readonly=True, select=True)
    write_date = fields.Datetime(string='Last Modification Date', readonly=True, select=True)
    date_start = fields.Datetime(string='Starting Date', default=fields.datetime.now(),select=True, copy=False)
    date_end = fields.Datetime(string='Ending Date', select=True, copy=False)
    date_assign = fields.Datetime(string='Assigning Date', select=True, copy=False, readonly=True)
    date_deadline = fields.Datetime(string='Deadline', select=True, copy=False)
    progress = fields.Integer(string="Working Time Progress(%)", copy=False, readonly=True)
    date_last_stage_update = fields.Datetime(string='Last Stage Update', select=True, default=fields.datetime.now(),copy=False, readonly=True)
    id = fields.Integer('ID', readonly=True)
    company_id = fields.Many2many('res.company', string='Company Name', default=lambda self: self.env['res.company']._company_default_get('car.workshop'))
    color = fields.Integer(string='Color Index')
    stage_id = fields.Many2one('worksheet.stages', string='Stage', track_visibility='onchange', copy=False)
    state = fields.Selection([
        ('waiting', 'Ready'),
        ('workshop_create_invoices', 'Invoiced'),
        ('cancel', 'Invoice Canceled'),
    ], string='Status', readonly=True, default='waiting', track_visibility='onchange', select=True)
    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=lambda self: [('res_model', '=', self._name)],
                                     auto_join=True, string='Attachments')
    displayed_image_id = fields.Many2one('ir.attachment',
                                         domain="[('res_model', '=', 'car.workshop'), ('res_id', '=', id),"
                                                "\ ('mimetype', 'ilike', 'image')]",
                                         string='Displayed Image')
    planned_works = fields.One2many('planned.work', 'work_id', string='Planned/Ordered Works')
    works_done = fields.One2many('planned.work', 'work_id', string='Work Done', domain=[('completed', '=', True)])
    materials_used = fields.One2many('material.used', 'material_id', string='Materials Used')
    remaining_hour = fields.Float(string='Remaining Hour', readonly=True, compute="hours_left")
    effective_hour = fields.Float(string='Hours Spent', readonly=True, compute="hours_spent")
    amount_total = fields.Float(string='Total Amount', readonly=True, compute="amount_total1")

    def _get_default_stages(self, cr, uid, context=None):
        """ Gives default stage_id """
        if context is None:
            context = {}
        default_vehicle_id = context.get('default_vehicle_id')
        if not default_vehicle_id:
            return False
        return self.find_stage(cr, uid, [], default_vehicle_id, [('fold', '=', False)], context=context)

    _defaults = {
        'stage_id': _get_default_stages,
    }

    @api.depends('planned_works.work_cost', 'materials_used.price')
    def amount_total1(self):
        for records in self:
            for hour in records:
                amount_totall = 0.0
                for line in hour.planned_works:
                    amount_totall += line.work_cost
                for line2 in hour.materials_used:
                    amount_totall += line2.price
                records.amount_total = amount_totall

    @api.multi
    def cancel(self):
        self.state = 'cancel'

    @api.multi
    def workshop_create_invoices(self):

        self.state = 'workshop_create_invoices'
        inv_obj = self.env['account.invoice']
        inv_line_obj = self.env['account.invoice.line']
        customer = self.partner_id
        if not customer.name:
            raise UserError(
                _(
                    'Please select a Customer.'))

        company_id = self.env['res.users'].browse(1).company_id
        currency_value = company_id.currency_id.id
        self.ensure_one()
        ir_values = self.env['ir.values']
        journal_id = ir_values.get_default('workshop.config.setting', 'invoice_journal_type')
        if not journal_id:
            journal_id = 1

        inv_data = {
            'name': customer.name,
            'reference': customer.name,
            'account_id': customer.property_account_receivable_id.id,
            'partner_id': customer.id,
            'currency_id': currency_value,
            'journal_id': journal_id,
            'origin': self.name,
            'company_id': company_id.id,
        }
        inv_id = inv_obj.create(inv_data)
        for records in self.planned_works:
            if records.planned_work.id :
                income_account = records.planned_work.property_account_income_id.id
            if not income_account:
                raise UserError(_('There is no income account defined for this product: "%s".') %
                                (records.planned_work.name,))

            inv_line_data = {
                'name': records.planned_work.name,
                'account_id': income_account,
                'price_unit': records.work_cost,
                'quantity': 1,
                'product_id': records.planned_work.id,
                'invoice_id': inv_id.id,
            }
            inv_line_obj.create(inv_line_data)

        for records in self.materials_used:
            if records.material.id :
                income_account = records.material.property_account_income_id.id
            if not income_account:
                raise UserError(_('There is no income account defined for this product: "%s".') %
                                (records.material.name,))

            inv_line_data = {
                'name': records.material.name,
                'account_id': records.material.property_account_income_id.id,
                'price_unit': records.price,
                'quantity': records.amount,
                'product_id': records.material.id,
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
        invoiced_records = self.env['car.workshop']

        total = 0
        for rows in invoiced_records:
            invoiced_date = rows.date
            invoiced_date = invoiced_date[0:10]
            if invoiced_date == str(date.today()):
                total = total + rows.price_subtotal
        for lines in self.materials_used:
            product_ids = self.env['product.product'].search(
                [('id', '=', lines.material.id)])
            for prod_id in product_ids:
                    move_id = self.env['stock.picking']
                    type_object = self.env['stock.picking.type']
                    company_id = self.env.context.get('company_id') or self.env.user.company_id.id
                    types = type_object.search([('code', '=', 'outgoing'), ('warehouse_id.company_id', '=', company_id)], limit=1)
                    vals = {
                        'partner_id': self.partner_id.id,
                        'origin': self.name,
                        'move_type': 'one',
                        'picking_type_id': types.id,
                        'location_id': types.default_location_src_id.id,
                        'location_dest_id': self.partner_id.property_stock_customer.id,
                        'move_lines': [(0, 0, {
                            'name': self.name,
                            'product_id': prod_id.id,
                            'product_uom': prod_id.uom_id.id,
                            'product_uom_qty': lines.amount,
                            'quantity_done': lines.amount,
                            'location_id': types.default_location_src_id.id,
                            'location_dest_id': self.partner_id.property_stock_customer.id,
                        })],
                    }
                    move = move_id.create(vals)
                    move.action_confirm()
                    move.action_assign()
                    move.action_done()
        return result

    @api.depends('works_done.duration')
    def hours_spent(self):
        for hour in self:
            effective_hour = 0.0
            for line in hour.works_done:
                effective_hour += line.duration
            self.effective_hour = effective_hour

    @api.depends('planned_works.time_spent')
    def hours_left(self):
        for hour in self:
            remaining_hour = 0.0
            for line in hour.planned_works:
                remaining_hour += line.time_spent
            self.remaining_hour = remaining_hour-self.effective_hour

    def process_demo_scheduler_queue(self):
        obj = self.env['car.workshop']
        obj1 = obj.search([])
        now = fields.Datetime.from_string(fields.Datetime.now())
        for obj2 in obj1:
            obj3 = obj2
            if obj3.stage_id.name != 'Done' and obj3.stage_id.name != 'Cancelled' and obj3.stage_id.name != 'Verified':
                end_date = fields.Datetime.from_string(obj3.date_deadline)
                start_date = fields.Datetime.from_string(obj3.date_assign)
                if obj3.date_deadline and obj3.date_assign and end_date > start_date:
                    if now < end_date:
                        diff1 = relativedelta(end_date, start_date)
                        if diff1.days == 0:
                            total_hr = int(diff1.minutes)
                        else:
                            total_hr = int(diff1.days) * 24 * 60 + int(diff1.minutes)
                        diff2 = relativedelta(now, start_date)
                        if diff2.days == 0:
                            current_hr = int(diff2.minutes)
                        else:
                            current_hr = int(diff2.days) * 24 * 60 + int(diff2.minutes)
                        if total_hr != 0:
                            obj3.progress = ((current_hr * 100) / total_hr)
                        else:
                            obj3.progress = 100
                    else:
                        obj3.progress = 100
                else:
                    obj3.progress = 0


    @api.model
    def _track_subtype(self, init_values):
        record = self.browse()
        if 'kanban_state' in init_values and record.kanban_state == 'blocked':
            return 'fleet_car_workshop.mt_task_blocked'
        elif 'kanban_state' in init_values and record.kanban_state == 'done':
            return 'fleet_car_workshop.mt_task_ready'
        elif 'user_id' in init_values and record.user_id:  # assigned -> new
            return 'fleet_car_workshop.mt_task_new'
        elif 'stage_id' in init_values and record.stage_id and record.stage_id.sequence <= 1:  # start stage -> new
            return 'fleet_car_workshop.mt_task_new'
        elif 'stage_id' in init_values:
            return 'fleet_car_workshop.mt_task_stage'
        return super(CarWorkshop, self)._track_subtype(init_values)

    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        context = dict(self.env.context, mail_create_nolog=True)

        # for default stage
        if vals.get('vehicle_id') and not context.get('default_vehicle_id'):
            context['default_vehicle_id'] = vals.get('vehicle_id')
        # user_id change: update date_assign
        if vals.get('user_id'):
            vals['date_assign'] = fields.Datetime.now()
        task = super(CarWorkshop, self.with_context(context)).create(vals)
        return task

    @api.multi
    def write(self, vals):
        now = fields.Datetime.now()
        # stage change: update date_last_stage_update
        if 'stage_id' in vals:
            vals['date_last_stage_update'] = now
            # reset kanban state when changing stage
            if 'kanban_state' not in vals:
                vals['kanban_state'] = 'normal'
        # user_id change: update date_assign
        if vals.get('user_id'):
            vals['date_assign'] = now

        result = super(CarWorkshop, self).write(vals)

        return result

    def _read_group_stages(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None, context=None):
        if context is None:
            context = {}
        stage_obj = self.pool.get('worksheet.stages')
        order = stage_obj._order
        access_rights_uid = access_rights_uid or uid
        if read_group_order == 'stage_id desc':
            order = '%s desc' % order
        if 'default_vehicle_id' in context:
            search_domain = ['|', ('vehicle_ids', '=', context['default_vehicle_id']), ('id', 'in', ids)]
        else:
            search_domain = [('id', 'in', ids)]
        stage_ids = stage_obj._search(cr, uid, search_domain, order=order, access_rights_uid=access_rights_uid, context=context)
        result = stage_obj.name_get(cr, access_rights_uid, stage_ids, context=context)
        result.sort(lambda x, y: cmp(stage_ids.index(x[0]), stage_ids.index(y[0])))

        fold = {}
        for stage in stage_obj.browse(cr, access_rights_uid, stage_ids, context=context):
            fold[stage.id] = stage.fold or False
        return result, fold

    _group_by_full = {
        'stage_id': _read_group_stages,
    }

    @api.cr_uid_ids_context
    def onchange_vehicle(self, cr, uid, id, vehicle_id, context=None):
        values = {}
        if vehicle_id:
            vehicle = self.pool.get('fleet.vehicle').browse(cr, uid, vehicle_id, context=context)
            if vehicle.exists():
                values['partner_id'] = vehicle.partner_id.id
                values['stage_id'] = self.find_stage(cr, uid, [], vehicle_id, [('fold', '=', False)], context=context)
        else:
            values['stage_id'] = False
        return {'value': values}

    def _get_default_vehicle(self, cr, uid, context=None):
        if context is None:
            context = {}
        if 'default_vehicle_id' in context:
            vehicle = self.pool.get('car.car').browse(cr, uid, context['default_vehicle_id'], context=context)
            if vehicle and vehicle.partner_id:
                return vehicle.partner_id.id
        return False

    def find_stage(self, cr, uid, cases, section_id, domain=[], order='sequence', context=None):
        """ Override of the base.stage method
            Parameter of the stage search taken from the lead:
            - section_id: if set, stages must belong to this section or
              be a default stage; if not set, stages must be default
              stages
        """
        if isinstance(cases, (int, long)):
            cases = self.browse(cr, uid, cases, context=context)
        section_ids = []
        if section_id:
            section_ids.append(section_id)
        for task in cases:
            if task.vehicle_id:
                section_ids.append(task.vehicle_id.id)
        search_domain = []
        if section_ids:
            search_domain = [('|')] * (len(section_ids) - 1)
            for section_id in section_ids:
                search_domain.append(('vehicle_ids', '=', section_id))
        search_domain += list(domain)
        stage_ids = self.pool.get('worksheet.stages').search(cr, uid, search_domain, order=order, context=context)
        if stage_ids:
            return stage_ids[0]
        return False
