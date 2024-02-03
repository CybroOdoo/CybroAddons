# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v (odoo@cybrosys.com)
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
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    """Model for extending the product template to include
     pack-related fields."""
    _inherit = 'product.template'

    def default_pack_location(self):
        """ Get the default pack location for the current company."""
        company_user = self.env.company
        warehouse = self.env['stock.warehouse'].search([(
            'company_id', '=', company_user.id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id

    is_pack = fields.Boolean(string='Is a Pack', help='Indicates whether the'
                                                      'product is a pack or '
                                                      'not.')
    pack_price = fields.Integer(string="Pack Price", compute='set_pack_price',
                                store=True,
                                help='The calculated price of the pack.')
    pack_products_ids = fields.One2many('pack.products', 'product_tmpl_id',
                                        string='Pack Products', copy=True,
                                        help='The list of products included '
                                             'in the pack.')
    pack_quantity = fields.Integer(string='Pack Quantity',
                                   help='The quantity of the product'
                                        ' in the pack.')
    pack_location_id = fields.Many2one('stock.location',
                                       domain=[('usage', 'in',
                                                ['internal', 'transit'])],
                                       default=default_pack_location,
                                       string='Pack Location',
                                       help='The default location for the pack.')

    @api.onchange('is_pack')
    def _onchange_is_pack(self):
        """Method _onchange_is_pack to trigger when any change in the
        field is_pack"""
        if self.is_pack:
            self.invoice_policy = 'delivery'

    @api.constrains('invoice_policy')
    def _check_invoice_policy(self):
        """Method _check_invoice_policy to whether the product is a pack
        product"""
        if self.invoice_policy != 'delivery' and self.is_pack:
            raise ValidationError(
                _("Pack products invoicing policy should be in delivered "
                  "quantities"))

    @api.depends('pack_products_ids', 'pack_products_ids.price')
    def set_pack_price(self):
        """Compute the pack price based on the prices of the pack products."""
        price = 0
        for record in self:
            for line in record.pack_products_ids:
                price = price + line.price
            record.pack_price = price

    @api.model
    def create(self, values):
        """Override the create method to add validation for pack products."""
        if values.get('is_pack', False):
            if not values.get('pack_products_ids', []):
                raise UserError(_(
                    'You need to add least one product in the Pack...!'))
            if values.get('type', False) == 'service':
                raise UserError(
                    _('You cannot define a pack product as a service..!'))
            if values.get('invoice_policy') == 'order':
                values['invoice_policy'] = 'delivery'
        return super().create(values)

    def write(self, values):
        """Override the write method to add validation for pack products."""
        super().write(values)
        for rec in self:
            if rec.is_pack:
                if not rec.pack_products_ids:
                    raise UserError(_(
                        'You need to add at least one product in the Pack...!'))
                if rec.type == 'service':
                    raise UserError(
                        _('You cannot define a pack product as a service..!'))

    def update_price_product(self):
        """Update the list price of the product with the pack price."""
        self.list_price = self.pack_price

    def get_quantity(self):
        """Calculate the pack quantity based on the availability of
        pack products."""
        total_quantity = 1
        flag = 1
        max_iterations = 1000
        while flag and total_quantity < max_iterations:
            for line in self.pack_products_ids:
                if line.qty_available >= line.quantity * total_quantity:
                    continue
                else:
                    if line.product_id.type != 'product':
                        continue
                    flag = 0
                    break
            if flag:
                total_quantity += 1
        self.pack_quantity = total_quantity - 1

    def update_quantity(self):
        """Update the pack quantity in the specified pack location."""
        company_user = self.env.company
        product_id = len(
            self.product_variant_ids) == 1 and self.product_variant_id.id
        location_id = self.pack_location_id.id
        if not location_id:
            warehouse = self.env['stock.warehouse'].search([(
                'company_id', '=', company_user.id)], limit=1)
            location_id = warehouse.lot_stock_id.id
            if not location_id:
                raise UserError(_(
                    'You need to select the location to update the pack '
                    'quantity...!'))
        existing_quantity = self.env['stock.quant'].search([('product_id', '=', product_id)], limit=1)
        if not existing_quantity:
            self.env['stock.quant'].with_context(inventory_mode=True).sudo().create(
                {
                    'product_id': product_id,
                    'location_id': location_id,
                    'quantity': self.pack_quantity,
                })
        else:
            existing_quantity.quantity = self.pack_quantity

    @api.onchange('pack_location_id')
    def change_quantity_based_on_location(self):
        """Update the total available quantity of pack products based
        on the selected pack location."""
        for line in self.pack_products_ids:
            stock_quant = self.env['stock.quant'].search(
                [('product_id', '=', line.product_id.id), (
                    'location_id', '=', self.pack_location_id.id)])
            if stock_quant:
                line.total_available_quantity = stock_quant.quantity
            else:
                line.total_available_quantity = stock_quant.quantity


class PackProducts(models.Model):
    """Model for selecting pack products.This model allows users to select
    and manage pack products. """
    _name = 'pack.products'
    _rec_name = 'product_tmpl_id'
    _description = 'Select Pack Products'

    product_id = fields.Many2one('product.product', string='Product',
                                 required=True,
                                 domain=[('is_pack', '=', False)],
                                 help='The specific product being referenced.')
    product_tmpl_id = fields.Many2one('product.template', string='Product',
                                      help='The template of the product.')
    price = fields.Float(string='Price', compute='compute_price', store=True,
                         help='The calculated price of the product.')
    quantity = fields.Integer(string='Quantity', default=1,
                              help='The quantity of the product.')
    qty_available = fields.Float(string='Quantity Available',
                                 compute='compute_quantity_of_product',
                                 store=True, readonly=False,
                                 help='The available quantity of the product.')
    total_available_quantity = fields.Float(string='Total Quantity',
                                            help='The total available '
                                                 'quantity of the selected '
                                                 'product.')

    @api.depends('product_id', 'total_available_quantity',
                 'product_id.qty_available')
    def compute_quantity_of_product(self):
        """Compute the available quantity for each record based on the
        product and location. """
        for record in self:
            location_id = record.product_tmpl_id.pack_location_id
            if location_id:
                stock_quant = self.env['stock.quant'].search(
                    [('product_id', '=', record.product_id.id),
                     ('location_id', '=', location_id.id)])
                if stock_quant:
                    record.qty_available = stock_quant.quantity
                else:
                    record.qty_available = False
            else:
                record.qty_available = False

    @api.depends('product_id', 'quantity')
    def compute_price(self):
        """ Compute the price for each record based on the product and quantity.
            """
        for record in self:
            record.price = record.product_id.lst_price * record.quantity

    @api.onchange('quantity')
    def set_price(self):
        """ Update the price field when the quantity changes."""
        self.price = self.product_id.lst_price * self.quantity

    @api.constrains('quantity')
    def _check_positive_qty(self):
        """Ensure that the quantity is always positive.Raises a validation
        error if any of the records have a negative quantity."""
        if any([ml.quantity < 0 for ml in self]):
            raise ValidationError(_('You can not enter negative quantities.'))
