# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
import logging
from prestapyt import PrestaShopWebServiceDict, PrestaShopWebServiceError
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tests import Form

_logger = logging.getLogger(__name__)


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
    state = fields.Selection(
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
        help="Export products to prestashop")
    is_product_imported = fields.Boolean(
        help='Check if the product is imported or not')
    is_product_exported = fields.Boolean(
        help='Check if the product is exported or not')
    import_contacts_button = fields.Boolean(
        string='Import Contacts',
        help="Import contacts from prestashop")
    export_contacts_button = fields.Boolean(
        string='Export Contacts',
        help="Export contacts to prestashop")
    is_contacts_imported = fields.Boolean(
        help='Whether contacts have been imported or not'
    )
    is_contacts_exported = fields.Boolean(
        help='Whether contacts have been exported or not'
    )
    import_orders_button = fields.Boolean(
        string='Import Orders',
        help="Import orders from prestashop")
    export_orders_button = fields.Boolean(
        string='Export Orders',
        help="Export orders to prestashop")
    is_order_imported = fields.Boolean(
        help='Check if the order is imported or not'
    )
    is_order_exported = fields.Boolean(
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
    def _check_connection(self):
        """Method to validate connection credentials."""
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
                if isinstance(stock_availables['stock_availables'][
                            'stock_available'], list):
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
                        "type": "consu",
                        "is_storable": True,
                        "weight": product_weight,
                        "prestashop": products['attrs']['id']
                    })
                    self.env['stock.quant'].create({
                        'product_id': product.id,
                        'quantity': available_quantity,
                        'location_id': self.env.ref(
                            'stock.location_stock').id,
                    })
                else:
                    self.env['stock.quant'].search(
                        [('product_id.name', '=', name)]).write(
                        {'quantity': available_quantity})
            if self.is_product_imported:
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Products imported successfully.',
                            'type': 'success', 'sticky': False}}
            else:
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'No new products to import.',
                            'type': 'danger', 'sticky': False}}
        except PrestaShopWebServiceError as e:
            raise UserError(e)

    def action_export_products(self):
        """Method to export products from Odoo to PrestaShop"""
        try:
            if self.state == 'not_connected':
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Instance is not connected with '
                                       'PrestaShop!',
                            'type': 'danger', 'sticky': False}}
            self.is_product_exported = False
            for product in self.env['product.product'].search([], limit=None):
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
                    if reference:
                        reference = str(reference)[:64]
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
                    }

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
                            'message': 'There are no new products to export',
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
                            'message': 'Contacts imported successfully.',
                            'type': 'success', 'sticky': False}}
            else:
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'There are no new contacts to import.',
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

            for customer in self.env['res.partner'].search([], limit=None):
                full_name = customer.name if customer.name else "nil nil"
                names = full_name.split()
                first_name = names[0]
                last_name = names[1] if len(names) > 1 else first_name
                if "." in first_name or "(" in first_name:
                    first_name = first_name.split(".")[0].split("(")[0]
                if "(" in last_name or "." in last_name:
                    last_name = last_name.split("(")[0].split(".")[0]

                existing_customer = False
                if customer.prestashop:
                    existing_customer = presta.search(
                        'customers', {'filter[id]': customer.prestashop})

                if not existing_customer and customer.email:
                    email_clean = customer.email.strip()
                    existing_customer = presta.search(
                        'customers', {'filter[email]': email_clean})

                    if existing_customer:
                        customer.write({'prestashop': existing_customer[0]})
                        self.is_contacts_exported = True

                if not existing_customer:
                    email_to_use = customer.email.strip() if customer.email else f"{first_name}_{customer.id}_pleasechange@email.com"
                    new_customer = {
                        'firstname': first_name,
                        'lastname': last_name,
                        'email': email_to_use,
                        'passwd': '',
                        'active': 1,
                        'company': customer.company_id.name if
                        customer.company_id.name else " ",
                        'id_default_group': 3,
                    }

                    try:
                        customer_id = presta.add(
                            'customers', {'customer': new_customer})
                        customer.write({
                            'prestashop': customer_id['prestashop']['customer'][
                                'id']
                        })
                        self.is_contacts_exported = True
                    except PrestaShopWebServiceError as e:
                        if 'email' in str(e).lower() or 'already used' in str(e).lower():
                            if customer.email:
                                email_clean = customer.email.strip()
                                existing = presta.search(
                                    'customers', {'filter[email]': email_clean}) or presta.search(
                                    'customers', {'filter[email]': f'[{email_clean}]'})
                                if existing:
                                    customer.write({'prestashop': existing[0]})
                                    self.is_contacts_exported = True
                        else:
                            raise UserError(f"Failed to export contact '{customer.name}': {e}")

                if customer.prestashop:
                    existing_address = presta.search(
                        'addresses', {'filter[id_customer]': customer.prestashop})
                    if not existing_address:
                        try:
                            address = {'address': {
                                'id_customer': customer.prestashop,
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
                        except PrestaShopWebServiceError as e:
                            raise UserError(f"Failed to export address for '{customer.name}'. Ensure the API key has permissions for 'addresses', 'countries', and 'states'. Original error: {e}")
            if self.is_contacts_exported:
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Contacts exported successfully.',
                            'type': 'success', 'sticky': False}}
            else:
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'There are no new contacts to export.',
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
            orders_data = orders.get('orders', {}).get('order', [])

            if not isinstance(orders_data, list):
                orders_data = [orders_data] if orders_data else []

            def get_or_create_product(product_presta_id, reference=""):
                prod = self.env['product.product'].search(
                    [('prestashop', '=', product_presta_id)], limit=1)
                if not prod:
                    try:
                        p_res = presta.get('products', product_presta_id)
                        p_info = p_res.get('product', {})
                        p_name = p_info.get('name', {})
                        name_str = ""
                        if isinstance(p_name, dict) and 'language' in p_name:
                            langs = p_name['language']
                            if isinstance(langs, list) and len(langs) > 0:
                                name_str = langs[0].get('value', '')
                            elif isinstance(langs, dict):
                                name_str = langs.get('value', '')
                        if not name_str:
                            name_str = reference or f"PrestaShop Product {product_presta_id}"
                        prod = self.env['product.product'].create({
                            'name': name_str,
                            'prestashop': int(product_presta_id) if str(product_presta_id).isdigit() else 0,
                        })
                    except Exception:
                        prod = self.env['product.product'].create({
                            'name': reference or f"PrestaShop Product {product_presta_id}",
                            'prestashop': int(product_presta_id) if str(product_presta_id).isdigit() else 0,
                        })
                return prod.id

            self.is_order_imported = False
            for orders_id in orders_data:
                order_id = orders_id['attrs']['id']
                order = presta.get('orders', order_id)
                if str(order['order']['current_state']) != '6':
                    customer_id = order['order']['id_customer']
                    partner = self.env['res.partner'].search(
                        [('prestashop', '=', customer_id)], limit=1)
                    if not partner:
                        try:
                            cust_res = presta.get('customers', customer_id)
                            cust_info = cust_res.get('customer', {})
                            first_name = cust_info.get('firstname', '')
                            last_name = cust_info.get('lastname', '')
                            email = cust_info.get('email', '')
                            name = f"{first_name} {last_name}".strip() or f"PrestaShop Customer {customer_id}"

                            if email:
                                partner = self.env['res.partner'].search(
                                    [('email', '=', email)], limit=1)
                            if partner:
                                partner.write({'prestashop': int(customer_id) if str(customer_id).isdigit() else 0})
                            else:
                                partner = self.env['res.partner'].create({
                                    'name': name,
                                    'email': email,
                                    'prestashop': int(customer_id) if str(customer_id).isdigit() else 0,
                                })
                        except Exception:
                            partner = self.env['res.partner'].create({
                                'name': f"PrestaShop Customer ({customer_id})",
                                'prestashop': int(customer_id) if str(customer_id).isdigit() else 0,
                            })
                    partner_id = partner.id
                    order_id = order['order']['id']
                    shipping = order['order']['total_shipping_tax_incl']
                    discount = order['order']['total_discounts_tax_incl']

                    existing_so = self.env['sale.order'].search(
                        [('prestashop', '=', order_id)], limit=1)
                    if not existing_so.prestashop:
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
                                     ('type', '=', 'service'),
                                     ('default_code', '=', 'Prestashop')])
                                if delivery_product:
                                    product = delivery_product
                                else:
                                    product = self.env[
                                        'product.product'].create({
                                        'name': 'Delivery charges',
                                        'default_code': 'Prestashop',
                                        "type": "service",
                                        'is_delivery_product': True
                                    })

                                carrier = self.env['delivery.carrier'].create({
                                    'name': 'Delivery(Prestashop)',
                                    'product_id': product.id,
                                    "is_prestashop_carrier": True
                                })
                            delivery_wizard = Form(
                                self.env[
                                    'choose.delivery.carrier'].with_context(
                                    default_order_id=sale_order.id,
                                    default_carrier_id=carrier.id
                                ))
                            choose_delivery_carrier = delivery_wizard.save()
                            choose_delivery_carrier.button_confirm()
                            delivery_line = sale_order.order_line
                            delivery_line.write({'price_unit': shipping,
                                                 'tax_ids': False})

                        if float(discount) > 0.0:
                            discount_product = self.env[
                                'product.product'].search(
                                [('is_discount_product', '=', True),
                                 ('type', '=', 'service')])
                            if discount_product:
                                add_discount = discount_product
                            else:
                                add_discount = self.env[
                                    'product.product'].create(
                                    {'name': 'Discounts',
                                     'type': 'service',
                                     'is_discount_product': True,
                                     'default_code': 'Prestashop'})
                            sale_order.update({
                                'order_line': [(fields.Command.create({
                                    'product_id': add_discount.id,
                                    'product_uom_qty': 1,
                                    'price_unit': -abs(float(discount)),
                                    'name': add_discount.name,
                                    'sequence': 500,
                                    'tax_ids': False
                                }))]})

                        order_rows = order.get('order', {}).get('associations', {}).get('order_rows', {}).get('order_row', [])
                        if not isinstance(order_rows, list):
                            order_rows = [order_rows] if order_rows else []

                        line_commands = []
                        for order_line in order_rows:
                            prod_id = get_or_create_product(
                                order_line.get('product_id'),
                                order_line.get('product_reference', '')
                            )
                            line_commands.append(fields.Command.create({
                                'product_id': prod_id,
                                'product_uom_qty': float(order_line.get('product_quantity', 1)),
                                'name': order_line.get('product_reference') or "PrestaShop Item",
                                'sequence': 1,
                                'tax_ids': False
                            }))
                        if line_commands:
                            sale_order.update({'order_line': line_commands})
            if self.is_order_imported:
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Orders imported successfully.',
                            'type': 'success', 'sticky': False}}
            else:
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'There are no new orders to import.',
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

            presta = PrestaShopWebServiceDict(self.api_url, self.api_key)
            self.is_order_exported = False
            skipped_orders = []

            for sale_order in self.env['sale.order'].search(
                    [('state', '=', 'sale')]):

                if sale_order.prestashop:
                    existing_orders = presta.search('orders', {
                        'filter[id]': sale_order.prestashop})
                    if existing_orders:
                        continue

                partner = sale_order.partner_id
                if not partner.prestashop:
                    if partner.email:
                        email_clean = partner.email.strip()
                        existing_cust = presta.search(
                            'customers', {'filter[email]': email_clean}) or presta.search(
                            'customers', {'filter[email]': f'[{email_clean}]'})
                        if existing_cust:
                            partner.write({'prestashop': existing_cust[0]})
                    if not partner.prestashop:
                        full_name = partner.name if partner.name else "nil nil"
                        names = full_name.split()
                        first_name = names[0]
                        last_name = names[1] if len(names) > 1 else first_name
                        if "." in first_name or "(" in first_name:
                            first_name = first_name.split(".")[0].split("(")[0]
                        if "(" in last_name or "." in last_name:
                            last_name = last_name.split("(")[0].split(".")[0]
                        email_to_use = partner.email.strip() if partner.email else f"{first_name}_{partner.id}_pleasechange@email.com"
                        new_cust = {
                            'firstname': first_name,
                            'lastname': last_name,
                            'email': email_to_use,
                            'passwd': '',
                            'active': 1,
                            'company': partner.company_id.name if partner.company_id.name else " ",
                            'id_default_group': 3,
                        }
                        try:
                            c_resp = presta.add('customers', {'customer': new_cust})
                            partner.write({'prestashop': c_resp['prestashop']['customer']['id']})
                        except PrestaShopWebServiceError as e:
                            if ('email' in str(e).lower() or 'already used' in str(e).lower()) and partner.email:
                                email_clean = partner.email.strip()
                                existing = presta.search('customers', {'filter[email]': email_clean}) or presta.search('customers', {'filter[email]': f'[{email_clean}]'})
                                if existing:
                                    partner.write({'prestashop': existing[0]})

                id_customer = partner.prestashop
                if not id_customer:
                    skipped_orders.append(
                        (sale_order.name, f"Customer '{partner.name}' could not be created/found in PrestaShop")
                    )
                    continue

                id_address = presta.search("addresses", {'filter[id_customer]': id_customer})
                if not id_address:
                    full_name = partner.name if partner.name else "nil nil"
                    names = full_name.split()
                    first_name = names[0]
                    last_name = names[1] if len(names) > 1 else first_name
                    if "." in first_name or "(" in first_name:
                        first_name = first_name.split(".")[0].split("(")[0]
                    if "(" in last_name or "." in last_name:
                        last_name = last_name.split("(")[0].split(".")[0]
                    try:
                        address_payload = {'address': {
                            'id_customer': id_customer,
                            'id_country': presta.search('countries', {
                                'filter[name]': partner.country_id.name})[
                                0] if partner.country_id.name else 21,
                            'id_state': presta.search('states', {
                                'filter[name]': partner.state_id.name})[
                                0] if partner.state_id.name else 1,
                            'alias': 'my address',
                            'lastname': last_name,
                            'firstname': first_name,
                            'address1': partner.street or partner.city or "please change",
                            'city': partner.city if partner.city else "please change",
                        }}
                        presta.add('addresses', address_payload)
                        id_address = presta.search("addresses", {'filter[id_customer]': id_customer})
                    except Exception as e:
                        _logger.warning(
                            "Failed to create address for customer '%s' "
                            "during order export: %s", partner.name, e)

                if not id_address:
                    skipped_orders.append(
                        (sale_order.name, f"No address found in PrestaShop for customer '{partner.name}'")
                    )
                    continue

                skip_order = False
                try:
                    address_detail = presta.get('addresses', id_address[0])
                    id_country = address_detail['address'].get('id_country', 0)
                    if id_country:
                        country_detail = presta.get('countries', id_country)
                        country_name = country_detail['country'].get(
                            'name', {}).get('language', [{}])
                        if isinstance(country_name, list):
                            country_name = country_name[0].get('value', f"ID {id_country}")
                        elif isinstance(country_name, dict):
                            country_name = country_name.get('value', f"ID {id_country}")
                        is_active = country_detail['country'].get('active', '0')
                        if str(is_active) == '0':
                            skipped_orders.append(
                                (sale_order.name,
                                 f"Delivery address country '{country_name}' is not active in PrestaShop. "
                                 f"Please enable it under International > Countries.")
                            )
                            skip_order = True
                except Exception as e:
                    _logger.warning(
                        "Could not verify country status for order '%s': %s",
                        sale_order.name, e)

                if skip_order:
                    continue

                if sale_order.order_line:
                    for order_line in sale_order.order_line:
                        if not order_line.product_id.prestashop:
                            product = order_line.product_id
                            price = product.lst_price
                            wholesale_price = product.standard_price
                            name = product.name
                            reference = product.description_sale if product.description_sale else (
                                product.default_code if product.default_code else name)
                            if reference:
                                reference = str(reference)[:64]
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
                                        'language': [{'attrs': {'id': str(i)}, 'value': name} for i in range(1, 5)]
                                    },
                                    'name': {
                                        'language': [{'attrs': {'id': str(i)}, 'value': name} for i in range(1, 5)]
                                    }
                                }
                            }
                            try:
                                p_res = presta.add('products', new_product)
                                product.write({'prestashop': p_res['prestashop']['product']['id']})
                            except Exception as e:
                                _logger.warning(
                                    "Failed to export product '%s' to "
                                    "PrestaShop during order export: %s",
                                    product.name, e)

                    cart_list = []
                    missing_product = False
                    for order_line in sale_order.order_line:
                        if not order_line.product_id.prestashop:
                            skipped_orders.append((
                                sale_order.name,
                                f"Product '{order_line.product_id.name}' is not exported to PrestaShop"
                            ))
                            missing_product = True
                            break
                        cart_list.append({
                            'id_product': order_line.product_id.prestashop,
                            'id_product_attribute': '0',
                            'id_address_delivery': id_address[0],
                            'id_customization': '0',
                            'price_with_tax': round(
                                order_line.price_unit
                                * order_line.product_uom_qty, 2),
                            'quantity': order_line.product_uom_qty
                        })

                    if missing_product:
                        continue

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

                        grand_total = round(sale_order.amount_total or sum(
                            order_line.product_id.lst_price * order_line.product_uom_qty
                            for order_line in sale_order.order_line), 2)
                        total_products = sum(
                            sale_order.order_line.mapped('product_uom_qty'))

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
                            'total_products': total_products,
                            'total_products_wt': grand_total,
                            'conversion_rate': 1,
                            'shipping_cost_tax_excl': 0,
                        }

                        order = presta.add('orders', {'order': new_order})
                        prestashop_id = order['prestashop']['order']['id']
                        sale_order.write({'prestashop': prestashop_id})
                        self.is_order_exported = True

            if self.is_order_exported:
                if skipped_orders:
                    skip_lines = '\n'.join([f"• {name}: {reason}" for name, reason in skipped_orders])
                    return {'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': 'Partial Export Warning',
                                'message': f"Some orders were exported successfully, but the following were skipped:\n\n{skip_lines}",
                                'type': 'warning', 'sticky': True}}
                else:
                    return {'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'message': 'Orders exported successfully',
                                'type': 'success', 'sticky': False}}
            else:
                if skipped_orders:
                    skip_lines = '\n'.join([f"• {name}: {reason}" for name, reason in skipped_orders])
                    return {'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': 'Order Export Skipped',
                                'message': f"No orders were exported. The following orders were skipped:\n\n{skip_lines}",
                                'type': 'danger', 'sticky': True}}
                else:
                    return {'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'message': 'There are no new orders to export',
                                'type': 'danger', 'sticky': False}}

        except PrestaShopWebServiceError as e:
            raise UserError(e)
