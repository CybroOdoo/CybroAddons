# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from prestapyt import PrestaShopWebServiceDict, PrestaShopWebServiceError
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tests import Form


class PrestashopConnector(models.Model):
    """A class to represent the prestashop connector"""
    _name = "prestashop.connector"
    _description = "Prestashop Connector"

    name = fields.Char(string='Instance Name', required=True,
                       help='The name of the instance')
    api_url = fields.Char(string="API URL", required=True,
                          help="The Api Url to connect")
    api_key = fields.Char(string="API KEY", required=True,
                          help="The Api Key to connect")
    state = fields.Selection(string="State",
                             selection=[('not_connected', 'Not Connected'),
                                        ('connected', 'Connected')],
                             default="not_connected", help="State of the shop")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)
    import_products_button = fields.Boolean(
        string="Import Products",
        help="Import products from prestashop")
    export_products_button = fields.Boolean(
        string="Export Products",
        help="Export products from prestashop")
    is_product_imported = fields.Boolean(
        string='Is Product Imported',
        help='Check if the product is imported or not')
    is_product_exported = fields.Boolean(
        string='Is Product Exported',
        help='Check if the product is exported or not')
    import_contacts_button = fields.Boolean(
        string='Import Contacts',
        help="Import contacts from prestashop")
    export_contacts_button = fields.Boolean(
        string='Export Contacts',
        help="Export contacts from prestashop")
    is_contacts_imported = fields.Boolean(
        string='Is Contacts Imported',
        help='Check if the contacts is imported or not'
    )
    is_contacts_exported = fields.Boolean(
        string='Is Contacts Exported',
        help='Check if the contacts is exported or not'
    )
    import_orders_button = fields.Boolean(
        string='Import Orders',
        help="Import orders from prestashop")
    export_orders_button = fields.Boolean(
        string='Export Orders',
        help="Export orders from prestashop")
    is_order_imported = fields.Boolean(
        string='Is Order Imported',
        help='Check if the order is imported or not'
    )
    is_order_exported = fields.Boolean(
        string='Is Order Exported',
        help='Check if the order is exported or not'
    )

    def action_connect(self):
        """Method to connect prestashop with Odoo"""
        try:
            prestashop = PrestaShopWebServiceDict(self.api_url, self.api_key)
            shop_info = prestashop.get('shops')
            if shop_info:
                self.write({
                    'state': 'connected'
                })
        except Exception as error:
            raise UserError(error)

    @api.constrains('api_url', 'api_key')
    def check_connection(self):
        """Method to check connection"""
        try:
            prestashop = PrestaShopWebServiceDict(self.api_url, self.api_key)
            prestashop.get('shops')
        except Exception as error:
            raise UserError(error)

    def action_import_products(self):
        """Method to import products from prestashop to Odoo"""
        try:
            if self.state == 'not_connected':
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Instance is not connected with '
                                       'Prestashop !',
                            'type': 'danger', 'sticky': False}}

            presta = PrestaShopWebServiceDict(self.api_url, self.api_key)
            products = presta.get('products')
            self.is_product_imported = False
            for products in products['products']['product']:
                product = presta.get('products', products['attrs']['id'])
                sales_price = product['product']['price']
                product_weight = product['product']['weight']
                cost_price = product['product']['wholesale_price']
                stock_availables = presta.get('stock_availables', options={
                    "filter[id_product]": products['attrs']['id']})
                if type(stock_availables['stock_availables'][
                            'stock_available']) == list:
                    available_quantity = presta.get('stock_availables',
                                                    stock_availables[
                                                        'stock_availables']
                                                    ['stock_available'][0][
                                                        'attrs']['id'])[
                        'stock_available']['quantity']
                else:
                    available_quantity = presta.get('stock_availables',
                                                    stock_availables[
                                                        'stock_availables'][
                                                        'stock_available'][
                                                        'attrs']['id'])[
                        'stock_available']['quantity']
                name = product['product']['name']['language'][0][
                    'value'] if isinstance(
                    product['product']['name']['language'], list) else \
                    product['product']['name']['language']['value']
                if int(products['attrs']['id']) != self.env[
                    'product.product'].search([('prestashop', '=',
                                                products['attrs'][
                                                    'id'])]).prestashop:
                    self.is_product_imported = True
                    product = self.env['product.product'].create({
                        'name': name,
                        "list_price": sales_price,
                        "standard_price": cost_price,
                        "detailed_type": "product",
                        "weight": product_weight,
                        "prestashop": products['attrs']['id']
                    })
                    self.env['stock.quant'].create({
                        'product_id': product.id,
                        'quantity': available_quantity,
                        'location_id': 8
                    })
                else:
                    self.env['stock.quant'].search(
                        [('product_id.name', '=', name)]).write(
                        {'quantity': available_quantity})
            if self.is_product_imported:
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Product imported successfully',
                            'type': 'success', 'sticky': False}}
            else:
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'No new product to import',
                            'type': 'danger', 'sticky': False}}
        except PrestaShopWebServiceError as e:
            raise UserError(e)

    def action_export_products(self):
        """Method to export products from Odoo into PrestaShop"""
        try:
            self.is_product_exported = False
            for product in self.env['product.product'].search([]):
                presta = PrestaShopWebServiceDict(self.api_url, self.api_key)
                existing_product = presta.search(
                    'products', {'filter[id]': product.prestashop})
                if not existing_product:
                    self.is_product_exported = True

                    price = product.lst_price
                    wholesale_price = product.standard_price
                    name = product.name
                    reference = product.description_sale if product.description_sale \
                        else (
                        product.default_code if product.default_code else name)
                    new_product = {
                        'product': {
                            'id_shop_default': '1',
                            'state': '1',
                            'price': round(price, 2),
                            'reference': reference,
                            'wholesale_price': wholesale_price,
                            'active': '1',
                            'available_for_order': '1',
                            'show_price': '1',
                            'indexed': '1',
                            'visibility': 'both',
                            'link_rewrite': {
                                'language': [
                                    {'attrs': {'id': '1'}, 'value': name},
                                    {'attrs': {'id': '2'}, 'value': name},
                                    {'attrs': {'id': '3'}, 'value': name},
                                    {'attrs': {'id': '4'},
                                     'value': name}]},
                            'name': {
                                'language': [
                                    {'attrs': {'id': '1'}, 'value': name},
                                    {'attrs': {'id': '2'}, 'value': name},
                                    {'attrs': {'id': '3'}, 'value': name},
                                    {'attrs': {'id': '4'},
                                     'value': name}]}}
                    }  # Added closing brace for new_product dictionary here

                    product_id = presta.add('products', new_product)
                    presta_product_id = product_id['prestashop']['product'][
                        'id']

                    product.write({
                        "prestashop": presta_product_id
                    })

            if self.is_product_exported:

                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Products exported successfully',
                            'type': 'success', 'sticky': False}}
            else:
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'There is no new product to export',
                            'type': 'danger', 'sticky': False}}

        except PrestaShopWebServiceError as e:
            raise UserError(e)

    def action_import_contacts(self):
        """Method to import customers from prestashop to odoo"""
        try:
            if self.state == 'not_connected':
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Instance is not connected with '
                                       'Prestashop !',
                            'type': 'danger', 'sticky': False}}
            presta = PrestaShopWebServiceDict(self.api_url, self.api_key)
            customers = presta.get('customers')
            self.is_contacts_imported = False
            for customer_id in customers['customers']['customer']:
                customer = presta.get('customers', customer_id['attrs']['id'])
                last_name = customer['customer']['lastname']
                first_name = customer['customer']['firstname']
                prestashop = customer['customer']['id']
                email = customer['customer']['email']
                name = first_name + " " + last_name
                if int(customer_id['attrs']['id']) != self.env[
                    'res.partner'].search([('prestashop', '=',
                                            customer_id['attrs'][
                                                'id'])]).prestashop:
                    self.is_contacts_imported = True
                    self.env['res.partner'].create({
                        'name': name,
                        'email': email,
                        'prestashop': prestashop
                    })
            if self.is_contacts_imported:
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Contacts imported successfully',
                            'type': 'success', 'sticky': False}}
            else:
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'There is no new contacts to import',
                            'type': 'danger', 'sticky': False}}
        except PrestaShopWebServiceError as e:
            raise UserError(e)

    def action_export_contacts(self):
        """Method to export customers from odoo to prestashop"""
        try:
            if self.state == 'not_connected':
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Instance is not connected with '
                                       'Prestashop !',
                            'type': 'danger', 'sticky': False}}
            self.is_contacts_exported = False
            presta = PrestaShopWebServiceDict(self.api_url, self.api_key)

            for customer in self.env['res.partner'].search([]):

                existing_customer = presta.search(
                    'customers', {'filter[id]': customer.prestashop, })
                if not existing_customer:
                    self.is_contacts_exported = True
                    full_name = customer.name if customer.name else "nil nil"
                    names = full_name.split()
                    first_name = names[0]
                    last_name = names[1] if len(names) > 1 else first_name
                    if "." in first_name or "(" in first_name:
                        first_name = first_name.split(".")[0].split("(")[0]
                    if "(" in last_name or "." in last_name:
                        last_name = last_name.split("(")[0].split(".")[0]
                    new_customer = {
                        'firstname': first_name,
                        'lastname': last_name,
                        'email': customer.email if customer.email else first_name + "_pleasechange@email.com",
                        'passwd': '',
                        'active': 1,
                        'company': customer.company_id.name if
                        customer.company_id.name else " ",
                        'id_default_group': 3,
                    }

                    customer_id = presta.add(
                        'customers', {'customer': new_customer})
                    customer.write({
                        'prestashop': customer_id['prestashop']['customer'][
                            'id']
                    })
                    address = {'address': {
                        'id_customer': customer_id['prestashop']['customer'][
                            'id'],
                        'id_country': presta.search('countries', {
                            'filter[name]': customer.country_id.name})[
                            0] if customer.country_id.name else 21,
                        'id_state': presta.search('states', {
                            'filter[name]': customer.state_id.name})[
                            0] if customer.state_id.name else 1,
                        'alias': 'my address',
                        'lastname': last_name,
                        'firstname': first_name,
                        'address1': customer.city if customer.city else
                        "please change",
                        'city': customer.city if customer.city else
                        "please change",
                    }}
                    presta.add('addresses', address)
            if self.is_contacts_exported:
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Contacts exported successfully',
                            'type': 'success', 'sticky': False}}
            else:
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'There is no new contacts to export',
                            'type': 'danger', 'sticky': False}}
        except PrestaShopWebServiceError as e:
            raise UserError(e)

    def action_import_orders(self):
        """Method to import Orders from prestashop to odoo"""
        try:
            if self.state == 'not_connected':
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Instance is not connected with '
                                       'Prestashop !',
                            'type': 'danger', 'sticky': False}}
            presta = PrestaShopWebServiceDict(self.api_url, self.api_key)
            orders = presta.get('orders')
            orders_data = orders['orders']['order']

            # Convert to list if it's a single order
            if not isinstance(orders_data, list):
                orders_data = [orders_data]

            self.is_order_imported = False
            # for orders_id in orders['orders']['order']:
            for orders_id in orders_data:
                order_id = orders_id['attrs']['id']
                order = presta.get('orders', order_id)
                # order = presta.get('orders', 78)
                if order['order']['current_state'] != 6:
                    customer_id = order['order']['id_customer']
                    partner_id = self.env['res.partner'].search(
                        [('prestashop', '=', customer_id)]).id
                    order_id = order['order']['id']
                    shipping = order['order']['total_shipping_tax_incl']
                    discount = order['order']['total_discounts_tax_incl']

                    if int(order_id) != self.env['sale.order'].search(
                            [('prestashop', '=', order_id)]).prestashop:
                        self.is_order_imported = True
                        sale_order = self.env['sale.order'].create({
                            "prestashop": order_id,
                            "partner_id": partner_id
                        })
                        if float(shipping) > 0.0:
                            shipping_method = self.env[
                                'delivery.carrier'].search(
                                [('is_prestashop_carrier', '=', True),
                                 ('name', '=', 'Delivery(Prestashop)')])
                            if shipping_method:
                                carrier = shipping_method
                            else:
                                delivery_product = self.env[
                                    'product.product'].search(
                                    [('name', '=',
                                      "Delivery charges(Prestashop)"),
                                     ('is_delivery_product', '=', True),
                                     ('detailed_type', '=', 'service'),
                                     ('default_code', '=', 'Prestashop')])
                                if delivery_product:
                                    product = delivery_product
                                else:
                                    product = self.env[
                                        'product.product'].create({
                                        'name': 'Delivery charges',
                                        'default_code': 'Prestashop',
                                        "detailed_type": "service",
                                        'is_delivery_product': True
                                    })

                                carrier = self.env['delivery.carrier'].create({
                                    'name': 'Delivery(Prestashop)',
                                    'product_id': product.id,
                                    "is_prestashop_carrier": True
                                })
                            delivery_wizard = Form(
                                self.env[
                                    'choose.delivery.carrier'].with_context({
                                    'default_order_id': sale_order.id,
                                    'default_carrier_id': carrier.id
                                }))
                            choose_delivery_carrier = delivery_wizard.save()
                            choose_delivery_carrier.button_confirm()
                            delivery_line = sale_order.order_line
                            delivery_line.write({'price_unit': shipping,
                                                 'tax_id': False})

                        if float(discount) > 0.0:
                            discount_product = self.env[
                                'product.product'].search(
                                [('is_discount_product', '=', True),
                                 ('detailed_type', '=', 'service')])
                            if discount_product:
                                add_discount = discount_product
                            else:
                                add_discount = self.env[
                                    'product.product'].create(
                                    {'name': 'Discounts',
                                     'detailed_type': 'service',
                                     'is_discount_product': True,
                                     'default_code': 'Prestashop'})
                            sale_order.update({
                                'order_line': [(fields.Command.create({
                                    'product_id': add_discount.id,
                                    'product_uom_qty': 1,
                                    'price_unit': -abs(float(discount)),
                                    'name': add_discount.name,
                                    'sequence': 500,
                                    'tax_id': False
                                }))]})

                        if type(order['order']['associations']['order_rows'][
                                    'order_row']) == list:
                            sale_order.update({
                                'order_line': [(fields.Command.create({
                                    'product_id': self.env[
                                        'product.product'].search([(
                                        'prestashop',
                                        '=', order_line[
                                            'product_id'])]).id,
                                    'product_uom_qty': order_line[
                                        'product_quantity'],
                                    'name': order_line['product_reference'],
                                    'sequence': 1,
                                    'tax_id': False
                                })) for order_line in
                                    order['order']['associations'][
                                        'order_rows'][
                                        'order_row']]})
                        else:
                            sale_order.update(
                                {'order_line': [(fields.Command.create({
                                    'product_id': self.env[
                                        'product.product'].search([(
                                        'prestashop',
                                        '=',
                                        order['order'][
                                            'associations'][
                                            'order_rows'][
                                            'order_row'][
                                            'product_id'])]).id,
                                    'product_uom_qty':
                                        order['order']['associations'][
                                            'order_rows']['order_row'][
                                            'product_quantity'],
                                    'name': order['order']['associations'][
                                        'order_rows']['order_row'][
                                        'product_reference'],
                                    'sequence': 1,
                                    'tax_id': False
                                }))]
                                })
            if self.is_order_imported:
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Orders imported successfully',
                            'type': 'success', 'sticky': False}}
            else:
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'There is no new orders to import',
                            'type': 'danger', 'sticky': False}}
        except PrestaShopWebServiceError as e:
            raise UserError(e)

    def action_export_orders(self):
        """Method to export orders to PrestaShop from Odoo"""
        try:
            if self.state == 'not_connected':
                return {'type': 'ir.actions.client',

                        'tag': 'display_notification',
                        'params': {
                            'message': 'Instance is not connected with '
                                       'PrestaShop!',
                            'type': 'danger', 'sticky': False}}

            prestashop_dict = {}
            presta = PrestaShopWebServiceDict(self.api_url, self.api_key)
            self.is_order_exported = False

            for sale_order in self.env['sale.order'].search(
                    [('state', '=', 'sale')]):
                id_customer = sale_order.partner_id.prestashop

                id_address = presta.search("addresses",
                                           {'filter[id_customer]': id_customer})

                if sale_order.order_line:
                    cart_list = [
                        {'id_product': order_line.product_id.prestashop,
                         'id_product_attribute': '0',
                         'id_address_delivery': id_address[0],
                         'id_customization': '0',
                         'price_with_tax': 115.00,
                         'quantity': order_line.product_uom_qty} for order_line
                        in sale_order.order_line
                    ]

                    existing_orders = presta.search('orders', {
                        'filter[id]': sale_order.prestashop})
                    if not existing_orders:
                        cart_data = {
                            'id_currency': 1,
                            'id_lang': 1,
                            'id_customer': id_customer,
                            'id_address_invoice': id_address[0],
                            'associations': {
                                'cart_rows': {'cart_row': cart_list}
                            }
                        }

                        grand_total = sum(
                            order_line.product_id.lst_price * order_line.product_uom_qty
                            for order_line in sale_order.order_line)
                        total_products = sum(
                            sale_order.order_line.mapped('product_uom_qty'))

                        grand_total = round(grand_total, 2)
                        cart = presta.add('carts', {'cart': cart_data})
                        cart_id = cart['prestashop']['cart']['id']
                        new_order = {
                            'id_address_delivery': id_address[0],
                            'id_address_invoice': id_address[0],
                            'id_cart': cart_id,
                            'current_state': 1,
                            'id_currency': 1,
                            'id_lang': 1,
                            'id_customer': id_customer,
                            'id_carrier': 1,
                            'module': 'ps_wirepayment',
                            'payment': 'Bank Transfer',
                            'total_paid': grand_total,
                            'total_paid_real': grand_total,
                            # 'total_paid_tax_incl': grand_total,
                            'total_products': total_products,
                            'total_products_wt': grand_total,
                            'conversion_rate': 1,
                            'shipping_cost_tax_excl': 0,
                        }

                        self.is_order_exported = True
                        order = presta.add('orders', {'order': new_order})

                        # prestashop_order_id = order.get('prestashop', {}).get(
                        #     'order', {}).get('id')

                        prestashop = order['prestashop']['order']['id']
                        prestashop_dict.update({sale_order: prestashop})

            for record in prestashop_dict:
                record.write({'prestashop': prestashop_dict[record]})

            if self.is_order_exported:
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Orders exported successfully',
                            'type': 'success', 'sticky': False}}
            else:
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'There are no new orders to export',
                            'type': 'danger', 'sticky': False}}
        except PrestaShopWebServiceError as e:
            raise UserError(e)
