#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTextileMto(TransactionCase):
    """Test the textile flag of website orders and of the manufacturing
    orders created for sale orders."""

    @classmethod
    def setUpClass(cls):
        """Create a textile product replenished on order, with a BoM."""
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Weaver'})
        # The product only needs the MTO route: having a BoM makes the
        # warehouse manufacture it
        mto_route = cls.env.ref('stock.route_warehouse0_mto')
        mto_route.active = True
        cls.product = cls.env['product.product'].create({
            'name': 'Cotton Shirt', 'is_textile_product': True,
            'is_storable': True, 'route_ids': [Command.set(mto_route.ids)]})
        component = cls.env['product.product'].create({
            'name': 'Cotton Fabric', 'is_textile_product': True})
        cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'bom_line_ids': [Command.create({
                'product_id': component.id, 'product_qty': 2})],
        })

    def _confirmed_productions(self, textile, website=False):
        """Confirm a sale order of the product and return its MOs."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'is_textile_sale_order': textile,
            'website_id': website and self.env['website'].search([], limit=1).id,
            'order_line': [Command.create({
                'product_id': self.product.id, 'product_uom_qty': 3})],
        })
        order.action_confirm()
        productions = self.env['mrp.production'].search(
            [('origin', '=', order.name)])
        self.assertTrue(productions, "The sale order should create an MO")
        return productions

    def test_textile_sale_order(self):
        """The MO of a textile sale order is flagged as textile."""
        productions = self._confirmed_productions(textile=True)
        self.assertTrue(all(productions.mapped('is_textile_mrp_order')))

    def test_website_order(self):
        """A website order of a textile product is flagged as textile on
        confirmation, and so is its MO."""
        productions = self._confirmed_productions(textile=False, website=True)
        self.assertTrue(all(productions.mapped('is_textile_mrp_order')))
        order = self.env['sale.order'].search(
            [('name', '=', productions[0].origin)])
        self.assertTrue(order.is_textile_sale_order)

    def test_website_order_other_product(self):
        """A website order without textile products is not flagged."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'website_id': self.env['website'].search([], limit=1).id,
            'order_line': [Command.create({
                'product_id': self.env['product.product'].create(
                    {'name': 'Office Chair'}).id})],
        })
        order.action_confirm()
        self.assertFalse(order.is_textile_sale_order)

    def test_other_sale_order(self):
        """The MO of a normal sale order is not flagged as textile."""
        productions = self._confirmed_productions(textile=False)
        self.assertFalse(any(productions.mapped('is_textile_mrp_order')))
