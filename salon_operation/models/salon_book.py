from openerp import models, fields,api,http,SUPERUSER_ID, _
from openerp.addons.sale.sale import sale_order
from openerp.http import request
from datetime import timedelta
from dateutil import parser


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.one
    @api.onchange('char_id')
    def onchange_chair(self):
        self.employee_id = self.char_id.related_employee

    @api.one
    @api.onchange('employee_id')
    def onchange_employee(self):
        have_any = False
        for Each_Chair in self.env['salon.chair'].search([]):
            if self.employee_id == Each_Chair.related_employee:
                have_any = Each_Chair
        self.char_id = have_any

    employee_id = fields.Many2one('hr.employee', 'Dressing Person', store=True)
    char_id = fields.Many2one('salon.chair', string='Chair')
    state = fields.Selection([
            ('draft', 'Draft'),
            ('sent', 'Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Scheduled'),
            ('manual', 'To Invoice'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ], 'Status', readonly=True, copy=False, help="Gives the status of the quotation or sales order.\
              \nThe exception status is automatically set when a cancel operation occurs \
              in the invoice validation (Invoice Exception) or in the picking list process (Shipping Exception).\nThe 'Waiting Schedule' status is set when the invoice is confirmed\
               but waiting for the scheduler to run on the order date.", select=True)
    name = fields.Char('Order Reference', required=True, copy=False,
            readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, select=True)
    order_line = fields.One2many('sale.order.line', 'order_id', 'Items', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=True)

    @api.onchange('name')
    def onchange_name(self):
        request.session['name_schedule'] = self.name

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'sale.order', context=context) or '/'
        # ====================================================================================
            vals['name'] = vals['name'].replace('SO', 'NO-')
            if str(request.session.get('name_schedule')) == '/':
                vals['name'] = str(vals['name'])
            else:
                vals['name'] = str(vals['name']) + '  ' + str(request.session.get('name_schedule'))
            request.session['name_schedule'] = None
        # ====================================================================================
        if vals.get('partner_id') and any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id', 'fiscal_position']):
            defaults = self.onchange_partner_id(cr, uid, [], vals['partner_id'], context=context)['value']
            if not vals.get('fiscal_position') and vals.get('partner_shipping_id'):
                delivery_onchange = self.onchange_delivery_id(cr, uid, [], vals.get('company_id'), None, vals['partner_id'], vals.get('partner_shipping_id'), context=context)
                defaults.update(delivery_onchange['value'])
            vals = dict(defaults, **vals)
        ctx = dict(context or {}, mail_create_nolog=True)
        new_id = super(sale_order, self).create(cr, uid, vals, context=ctx)
        self.message_post(cr, uid, [new_id], body=_("Quotation created"), context=ctx)
        return new_id

    @api.one
    def get_warning(self):
        if self.for_month.booked:
            self.for_month = False
            self.month_state_show = '                    ' \
                                    '                     ' \
                                    'Sorry, this month is fully booked'
        else:
            self.month_state_show = ''

    @api.one
    def get_warning_for_day(self):
        if self.for_day.booked:
            self.for_day = False
            self.month_state_show = '                    ' \
                                    '                     ' \
                                    'Sorry, this day is fully booked'
        else:
            self.month_state_show = ' '

    @api.one
    def get_warning_for_time(self):
        if self.for_time.booked:
            self.for_time = False
            self.month_state_show = '                    ' \
                                    '                     ' \
                                    'Sorry, this time is fully booked'
        else:
            self.month_state_show = ' '
    @api.one
    def get_selected_month(self):
        return self.for_month.id

    @api.onchange('for_month')
    def onchange_month(self):
        # ====clear=other=fields=========
        self.for_day = False
        self.char_id = False
        self.for_time = False
        # ===============================
        self.get_warning()
        return {'domain': {'for_day': [('month_id', '=', self.get_selected_month()),
                                       ('day_type', '=', 'on'),
                                       ('booked', '=', False)]}}

    @api.one
    def get_selected_day(self):
        return self.for_day.id

    @api.onchange('for_day')
    def onchange_day(self):
        # ===Clear=other=fields=======
        self.char_id = False
        self.for_time = False
        # ============================
        self.get_warning_for_day()
        # for i in self.env['salon.period'].search([]):
        #     if i.day_id.id == False:
        #         print 'kkkkkkkk'
        selected_day = self.get_selected_day()
        if selected_day[0]:
            print ''
        else:
            selected_day = -1

        return {'domain': {'for_time': [('day_id', '=', selected_day), ('period_type', '=', 'on')]}}

    @api.one
    def get_selected_time(self):
        return self.for_time

    @api.onchange('for_time')
    def onchange_time(self):
        # ===Clear=other=fields=======
        self.char_id = False
        # ============================
        self.get_warning_for_time()
        chair_ids = []
        for Each_Period_line in self.get_selected_time()[0].chair_lines:
            if Each_Period_line.booked:
                chair_ids.append(Each_Period_line.chair_id.id)
        return {'domain': {'char_id': [('id', 'not in', chair_ids)]}}


    created_domain = [('booked', '=', False)]
    for_month = fields.Many2one('salon.month', domain=created_domain)
    for_day = fields.Many2one('salon.day', domain=[('month_id', '=', -1)])
    for_time = fields.Many2one('salon.period', domain=[('day_id', 'in', [-69]), [('day_id', '!=', None)]])
    month_state_show = fields.Char(default=' ')
