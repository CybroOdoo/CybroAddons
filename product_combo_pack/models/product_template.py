# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fansa Jabeen A (odoo@cybrosys.com)
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
    pack_price = fields.Integer(string="Pack Price", compute='_compute_set_pack_price',
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
    def _compute_set_pack_price(self):
        """Compute the pack price based on the prices of the pack products."""
        price = 0
        for record in self:
            for line in record.pack_products_ids:
                price = price + line.price
            record.pack_price = price

    @api.model
    def create(self, vals_list):
        """Override the create method to add validation for pack products."""
        for values in vals_list:  # loop through each record dict
            if values.get('is_pack', False):
                # Ensure at least one product in the pack
                if not values.get('pack_products_ids', []):
                    raise UserError(
                        _('You need to add at least one product in the Pack..!'))
                # A pack cannot be a service
                if values.get('type') == 'service':
                    raise UserError(
                        _('You cannot define a pack product as a service..!'))
                # Adjust invoice policy if needed
                if values.get('invoice_policy') == 'order':
                    values['invoice_policy'] = 'delivery'
        # Call super with the full list
        return super(ProductTemplate, self).create(vals_list)

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

    def action_update_price_product(self):
        """Update the list price of the product with the pack price."""
        self.list_price = self.pack_price

    def action_get_quantity(self):
        """Calculate the pack quantity based on the availability of
        pack products."""
        for pack in self:
            max_packs_list = []
            for pack_product in pack.pack_products_ids:
                if pack_product.quantity > 0:
                    max_packs = pack_product.qty_available // pack_product.quantity
                    max_packs_list.append(max_packs)
            # # Set the max packs as the minimum value in the list
            pack.pack_quantity = min(max_packs_list) if max_packs_list else 0

    def action_update_quantity(self):
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
    def _onchange_quantity_based_on_location(self):
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
