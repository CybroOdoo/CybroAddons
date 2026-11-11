################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
################################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestProductManagement(TransactionCase):
    """Comprehensive test suite for Product Management System wizards."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ProductTemplate = cls.env['product.template']
        cls.ProductProduct = cls.env['product.product']
        cls.ProductCategory = cls.env['product.category']
        cls.Partner = cls.env['res.partner']

        cls.test_category = cls.ProductCategory.create({'name': 'Test Category'})
        cls.new_category = cls.ProductCategory.create({'name': 'New Bulk Category'})

        cls.partner = cls.Partner.create({'name': 'Test Vendor Partner'})

        cls.product_1 = cls.ProductTemplate.create({
            'name': 'Bulk Test Product 1',
            'list_price': 10.0,
            'categ_id': cls.test_category.id,
        })
        cls.product_2 = cls.ProductTemplate.create({
            'name': 'Bulk Test Product 2',
            'list_price': 20.0,
            'categ_id': cls.test_category.id,
        })
        cls.product_3 = cls.ProductTemplate.create({
            'name': 'Bulk Test Product 3',
            'list_price': 30.0,
            'categ_id': cls.test_category.id,
        })

    def test_01_mass_price_update(self):
        """Verify bulk price updates on selected products."""
        wizard = self.env['product.update.price'].create({
            'product_ids': [(6, 0, [self.product_1.id, self.product_2.id])],
            'product_price': 55.0,
        })
        wizard.action_product_update_price_confirm()
        self.assertEqual(self.product_1.list_price, 55.0)
        self.assertEqual(self.product_2.list_price, 55.0)

    def test_02_mass_category_change(self):
        """Verify bulk category assignment."""
        wizard = self.env['product.category.change'].create({
            'product_ids': [(6, 0, [self.product_1.id, self.product_2.id])],
            'category_id': self.new_category.id,
        })
        wizard.action_product_category_change_confirm()
        self.assertEqual(self.product_1.categ_id.id, self.new_category.id)
        self.assertEqual(self.product_2.categ_id.id, self.new_category.id)

    def test_03_make_purchasable(self):
        """Verify bulk toggle of purchasable flag."""
        wizard = self.env['product.make.purchasable'].create({
            'product_ids': [(6, 0, [self.product_1.id, self.product_2.id])],
        })
        wizard.action_product_make_purchasable_confirm()
        self.assertTrue(self.product_1.purchase_ok)
        self.assertTrue(self.product_2.purchase_ok)

        wizard.action_product_make_purchasable_false()
        self.assertFalse(self.product_1.purchase_ok)
        self.assertFalse(self.product_2.purchase_ok)

    def test_04_make_salable(self):
        """Verify bulk toggle of salable flag."""
        wizard = self.env['product.make.salable'].create({
            'product_ids': [(6, 0, [self.product_1.id, self.product_2.id])],
        })
        wizard.action_product_make_salable_false()
        self.assertFalse(self.product_1.sale_ok)
        self.assertFalse(self.product_2.sale_ok)

        wizard.action_product_make_salable_confirm()
        self.assertTrue(self.product_1.sale_ok)
        self.assertTrue(self.product_2.sale_ok)

    def test_05_archive_products(self):
        """Verify bulk archiving."""
        wizard = self.env['product.archive'].create({
            'product_ids': [(6, 0, [self.product_3.id])],
        })
        wizard.action_archive_product()
        self.assertFalse(self.product_3.active)
        self.product_3.active = True  # reset

    def test_06_publish_products(self):
        """Verify bulk publishing and unpublishing."""
        wizard = self.env['product.publish'].create({
            'product_ids': [(6, 0, [self.product_1.id, self.product_2.id])],
        })
        wizard.action_publish_product()
        self.assertTrue(self.product_1.is_published)
        self.assertTrue(self.product_2.is_published)

        wizard.action_not_publish_product()
        self.assertFalse(self.product_1.is_published)
        self.assertFalse(self.product_2.is_published)

    def test_07_invoice_policy(self):
        """Verify bulk change of invoice policy."""
        wizard = self.env['product.invoice'].create({
            'product_ids': [(6, 0, [self.product_1.id, self.product_2.id])],
            'invoice_policy': 'delivery',
        })
        wizard.action_change_invoice_policy_products()
        self.assertEqual(self.product_1.invoice_policy, 'delivery')
        self.assertEqual(self.product_2.invoice_policy, 'delivery')

    def test_08_customer_lead_time(self):
        """Verify bulk customer lead time update."""
        wizard = self.env['product.customer.lead.time'].create({
            'product_ids': [(6, 0, [self.product_1.id])],
            'sale_delay': 5,
        })
        wizard.action_change_customer_lead_time()
        self.assertEqual(self.product_1.sale_delay, 5)

    def test_09_change_tracking(self):
        """Verify bulk product tracking change."""
        wizard = self.env['product.change.tracking'].create({
            'product_ids': [(6, 0, [self.product_1.id])],
            'tracking': 'lot',
        })
        wizard.action_change_product_tracking()
        self.assertEqual(self.product_1.tracking, 'lot')

        wizard_none = self.env['product.change.tracking'].create({
            'product_ids': [(6, 0, [self.product_1.id])],
            'tracking': 'none',
        })
        wizard_none.action_change_product_tracking()
        self.assertEqual(self.product_1.tracking, 'none')

    def test_10_customer_and_vendor_tax(self):
        """Verify bulk update of customer and vendor taxes."""
        tax_sale = self.env['account.tax'].search([('type_tax_use', '=', 'sale')], limit=1)
        if tax_sale:
            wizard_cust = self.env['product.customer.tax'].create({
                'product_ids': [(6, 0, [self.product_1.id])],
                'tax_ids': [(6, 0, [tax_sale.id])],
            })
            wizard_cust.action_change_customer_tax()
            self.assertIn(tax_sale, self.product_1.taxes_id)

        tax_purchase = self.env['account.tax'].search([('type_tax_use', '=', 'purchase')], limit=1)
        if tax_purchase:
            wizard_vendor = self.env['product.vendor.tax'].create({
                'product_ids': [(6, 0, [self.product_1.id])],
                'tax_ids': [(6, 0, [tax_purchase.id])],
            })
            wizard_vendor.action_change_vendor_tax()
            self.assertIn(tax_purchase, self.product_1.supplier_taxes_id)

    def test_11_website_category(self):
        """Verify bulk website category assignment."""
        web_cat = self.env['product.public.category'].create({'name': 'Public Web Cat'})
        wizard = self.env['product.category.website'].create({
            'product_ids': [(6, 0, [self.product_1.id])],
            'public_categ_ids': [(6, 0, [web_cat.id])],
        })
        wizard.action_change_website_category()
        self.assertIn(web_cat, self.product_1.public_categ_ids)

    def test_12_cross_sell_products(self):
        """Verify alternative, accessory, and optional product wizards."""
        # Alternative
        wiz_alt = self.env['product.alternative'].create({
            'product_ids': [(6, 0, [self.product_1.id])],
            'alternative_ids': [(6, 0, [self.product_2.id])],
        })
        wiz_alt.action_add_alternative_products()
        self.assertIn(self.product_2, self.product_1.alternative_product_ids)

        # Accessory
        variant_2 = self.product_2.product_variant_id
        wiz_acc = self.env['product.accessory'].create({
            'product_ids': [(6, 0, [self.product_1.id])],
            'accessory_ids': [(6, 0, [variant_2.id])],
        })
        wiz_acc.action_add_accessory_products()
        self.assertIn(variant_2, self.product_1.accessory_product_ids)

        # Optional
        wiz_opt = self.env['product.optional'].create({
            'product_ids': [(6, 0, [self.product_1.id])],
            'optional_ids': [(6, 0, [self.product_2.id])],
        })
        wiz_opt.action_add_optional_products()
        self.assertIn(self.product_2, self.product_1.optional_product_ids)

    def test_13_locations_update(self):
        """Verify bulk inventory and production location updates."""
        inv_loc = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
        if inv_loc:
            wiz_inv = self.env['product.inventory.location'].create({
                'product_ids': [(6, 0, [self.product_1.id])],
                'inventory_location_id': inv_loc.id,
            })
            wiz_inv.action_change_inventory_location()
            self.assertEqual(self.product_1.property_stock_inventory, inv_loc)

        prod_loc = self.env['stock.location'].search([('usage', '=', 'production')], limit=1)
        if prod_loc:
            wiz_prod = self.env['product.production.location'].create({
                'product_ids': [(6, 0, [self.product_1.id])],
                'production_location_id': prod_loc.id,
            })
            wiz_prod.action_change_production_location()
            self.assertEqual(self.product_1.property_stock_production, prod_loc)

    def test_14_add_vendor(self):
        """Verify bulk vendor addition."""
        currency = self.env.company.currency_id
        wizard = self.env['product.add.vendor'].create({
            'product_ids': [(6, 0, [self.product_1.id])],
            'vendor_ids': [(0, 0, {
                'partner_id': self.partner.id,
                'price': 15.0,
                'delay': 3,
                'currency_id': currency.id,
            })],
        })
        wizard.action_add_product_vendors()
        self.assertTrue(any(s.partner_id == self.partner for s in self.product_1.seller_ids))

    def test_15_add_attribute(self):
        """Verify bulk product attribute addition."""
        attr = self.env['product.attribute'].create({'name': 'Test Color'})
        val1 = self.env['product.attribute.value'].create({'name': 'Red', 'attribute_id': attr.id})
        val2 = self.env['product.attribute.value'].create({'name': 'Blue', 'attribute_id': attr.id})

        wizard = self.env['product.add.attribute'].create({
            'product_ids': [(6, 0, [self.product_1.id])],
            'attribute_line_ids': [(0, 0, {
                'attribute_id': attr.id,
                'value_ids': [(6, 0, [val1.id, val2.id])],
            })],
        })
        wizard.action_add_product_attributes()
        self.assertTrue(
            any(line.attribute_id == attr for line in self.product_1.attribute_line_ids),
        )

    def test_16_delete_product(self):
        """Verify bulk deletion."""
        product_to_del = self.ProductTemplate.create({'name': 'Product To Delete'})
        prod_id = product_to_del.id
        wizard = self.env['product.delete'].create({
            'product_ids': [(6, 0, [prod_id])],
        })
        wizard.action_delete_product()
        self.assertFalse(self.ProductTemplate.browse(prod_id).exists())
