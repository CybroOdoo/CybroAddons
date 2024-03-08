from odoo import models, fields, api
from datetime import datetime


class Washing(models.Model):
    """washing activity generating model"""
    _name = 'washing.washing'
    _description = 'Washing Washing'

    def start_wash(self):
        """
            Function for initiating the activity of washing.
        """
        if not self.laundry_works:
            self.laundry_obj.state = 'wash'
            self.laundry_obj.laundry_obj.state = 'process'
        for each in self:
            for obj in each.product_line:
                self.env['sale.order.line'].create(
                    {'product_id': obj.product_id.id,
                     'name': obj.name,
                     'price_unit': obj.price_unit,
                     'order_id': each.laundry_obj.laundry_obj.sale_obj.id,
                     'product_uom_qty': obj.quantity,
                     'product_uom': obj.uom_id.id,
                     })
        self.state = 'process'

    def set_to_done(self):
        self.state = 'done'

        f = 0
        if not self.laundry_works:
            if self.laundry_obj.extra_work:
                for each in self.laundry_obj.extra_work:
                    self.create({'name': each.name,
                                 'user_id': each.assigned_person.id,
                                 'description': self.laundry_obj.description,
                                 'laundry_obj': self.laundry_obj.id,
                                 'state': 'draft',
                                 'laundry_works': True,
                                 'washing_date': datetime.now().strftime(
                                     '%Y-%m-%d %H:%M:%S')})
                self.laundry_obj.state = 'extra_work'
        laundry_obj = self.search([('laundry_obj.laundry_obj', '=',
                                    self.laundry_obj.laundry_obj.id)])
        for each in laundry_obj:
            if each.state != 'done' or each.state == 'cancel':
                f = 1
                break
        if f == 0:
            self.laundry_obj.laundry_obj.state = 'done'
        laundry_obj1 = self.search([('laundry_obj', '=', self.laundry_obj.id)])
        f1 = 0
        for each in laundry_obj1:
            if each.state != 'done' or each.state == 'cancel':
                f1 = 1
                break
        if f1 == 0:
            self.laundry_obj.state = 'done'

    @api.depends('product_line')
    def get_total(self):
        total = 0
        for obj in self:
            for each in obj.product_line:
                total += each.subtotal
            obj.total_amount = total

    name = fields.Char(string='Work')
    laundry_works = fields.Boolean(default=False, invisible=1)
    user_id = fields.Many2one('res.users',
                              string='Assigned Person',
                              help="name of assigned person")
    washing_date = fields.Datetime(string='Date', help="date of washing")
    description = fields.Text(string='Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('process', 'Process'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, default='draft')
    laundry_obj = fields.Many2one('laundry.order.line', invisible=1)
    product_line = fields.One2many('wash.order.line', 'wash_obj',
                                   string='Products', ondelete='cascade')
    total_amount = fields.Float(compute='get_total', string='Grand Total')


class SaleOrderInherit(models.Model):
    """
        for creating orderlines in washing.
    """
    _name = 'wash.order.line'
    _description = 'Washing Order LINE'

    @api.depends('price_unit', 'quantity')
    def compute_amount(self):
        total = 0
        for obj in self:
            total += obj.price_unit * obj.quantity
        obj.subtotal = total

    wash_obj = fields.Many2one('washing.washing', string='Order Reference',
                               ondelete='cascade')
    name = fields.Text(string='Description', required=True)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure ', required=True)
    quantity = fields.Integer(string='Quantity')
    product_id = fields.Many2one('product.product', string='Product')
    price_unit = fields.Float('Unit Price', default=0.0,
                              related='product_id.list_price')
    subtotal = fields.Float(compute='compute_amount', string='Subtotal',
                            readonly=True, store=True)
