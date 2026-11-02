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
from lxml import etree

from odoo.fields import Domain
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTextileProductDomain(TransactionCase):
    """Test that textile orders only offer textile products."""

    @classmethod
    def setUpClass(cls):
        """Create a textile and a non textile product and a partner."""
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Weaver'})
        cls.textile = cls.env['product.product'].create({
            'name': 'Cotton Fabric', 'is_textile_product': True,
            'purchase_ok': True})
        cls.other = cls.env['product.product'].create({
            'name': 'Office Chair', 'purchase_ok': True})

    def _catalog_products(self, order):
        """Return the test products the order catalog would show."""
        return self.env['product.product'].search(
            order._get_product_catalog_domain()
            & Domain('id', 'in', (self.textile | self.other).ids))

    def test_sale_catalog(self):
        """Textile sale orders hide non textile products in the catalog."""
        orders = self.env['sale.order'].create([{
            'partner_id': self.partner.id, 'is_textile_sale_order': textile,
        } for textile in (True, False)])
        self.assertEqual(self._catalog_products(orders[0]), self.textile)
        self.assertEqual(self._catalog_products(orders[1]),
                         self.textile | self.other)

    def test_purchase_catalog(self):
        """Textile purchase orders hide non textile products in the
        catalog."""
        orders = self.env['purchase.order'].create([{
            'partner_id': self.partner.id,
            'is_textile_purchase_order': textile,
        } for textile in (True, False)])
        self.assertEqual(self._catalog_products(orders[0]), self.textile)
        self.assertEqual(self._catalog_products(orders[1]),
                         self.textile | self.other)

    def test_order_line_product_domain(self):
        """The order line product fields filter on the textile flag."""
        for model, fnames in (
                ('sale.order', ('product_id', 'product_template_id')),
                ('purchase.order', ('product_id',))):
            arch = self.env[model].get_view(view_type='form')['arch']
            for line_view in ('list', 'form'):
                for fname in fnames:
                    if line_view == 'form' and fname == 'product_template_id':
                        continue
                    node = etree.fromstring(arch).xpath(
                        f"//field[@name='order_line']/{line_view}"
                        f"//field[@name='{fname}']")[0]
                    self.assertIn('is_textile_product', node.get('domain'),
                                  f"{model} {line_view} {fname}")

    def test_mrp_product_domain(self):
        """The product to build of manufacturing orders and bills of
        materials, and the BoM of manufacturing orders, filter on the textile
        flag."""
        for model, fname in (('mrp.production', 'product_id'),
                             ('mrp.bom', 'product_tmpl_id')):
            arch = etree.fromstring(
                self.env[model].get_view(view_type='form')['arch'])
            node = arch.xpath(
                f"//sheet/group/group/field[@name='{fname}']")[0]
            self.assertIn('is_textile_product', node.get('domain'), model)
        arch = etree.fromstring(
            self.env['mrp.production'].get_view(view_type='form')['arch'])
        node = arch.xpath("//div[@name='bom_div']/field[@name='bom_id']")[0]
        self.assertIn('product_tmpl_id.is_textile_product', node.get('domain'))
