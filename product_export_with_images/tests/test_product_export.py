# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, HttpCase, tagged


@tagged('post_install', '-at_install')
class TestProductExportWizard(TransactionCase):
    """Test cases for the product.export wizard."""

    @classmethod
    def setUpClass(cls):
        super(TestProductExportWizard, cls).setUpClass()
        cls.ProductTemplate = cls.env['product.template']
        cls.ProductProduct = cls.env['product.product']
        cls.ExportWizard = cls.env['product.export']
        
        cls.category = cls.env['product.category'].create({'name': 'Test Category'})
        
        cls.product_tmpl = cls.ProductTemplate.create({
            'name': 'Test Product Template',
            'default_code': 'TPT1',
            'categ_id': cls.category.id,
            'list_price': 100.0,
            'standard_price': 50.0,
        })
        
        cls.product_variant = cls.ProductProduct.create({
            'name': 'Test Product Variant',
            'default_code': 'TPV1',
            'categ_id': cls.category.id,
            'list_price': 150.0,
            'standard_price': 75.0,
        })

    def test_01_action_export_products_template(self):
        """Test action_export_products with product.template active model."""
        wizard = self.ExportWizard.with_context(
            active_ids=self.product_tmpl.ids,
            active_model='product.template'
        ).create({})
        
        res = wizard.action_export_products()
        
        self.assertEqual(res.get('type'), 'ir.actions.act_url')
        self.assertEqual(res.get('target'), 'new')
        self.assertTrue(res.get('url').startswith('/products_download/excel_report/'))

    def test_02_action_export_products_variant(self):
        """Test action_export_products with product.product active model."""
        wizard = self.ExportWizard.with_context(
            active_ids=self.product_variant.ids,
            active_model='product.product'
        ).create({})
        
        res = wizard.action_export_products()
        
        self.assertEqual(res.get('type'), 'ir.actions.act_url')
        self.assertEqual(res.get('target'), 'new')
        self.assertTrue(res.get('url').startswith('/products_download/excel_report/'))

    def test_03_get_product_lines_template(self):
        """Test get_product_lines returns correct data for templates."""
        wizard = self.ExportWizard.create({
            'product_tmp_ids': [(6, 0, self.product_tmpl.ids)]
        })
        lines = wizard.get_product_lines()
        
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]['name'], 'Test Product Template')
        self.assertEqual(lines[0]['internal_reference'], 'TPT1')
        self.assertEqual(lines[0]['category'], 'Test Category')
        self.assertEqual(lines[0]['cost'], 50.0)
        self.assertEqual(lines[0]['sales_price'], 100.0)
        
    def test_04_get_product_lines_variant(self):
        """Test get_product_lines returns correct data for variants."""
        wizard = self.ExportWizard.create({
            'product_ids': [(6, 0, self.product_variant.ids)]
        })
        lines = wizard.get_product_lines()
        
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]['name'], 'Test Product Variant')
        self.assertEqual(lines[0]['internal_reference'], 'TPV1')
        self.assertEqual(lines[0]['category'], 'Test Category')
        self.assertEqual(lines[0]['cost'], 75.0)
        self.assertEqual(lines[0]['sales_price'], 150.0)


@tagged('post_install', '-at_install')
class TestProductExportController(HttpCase):
    """Test cases for the ExcelReportController."""

    def test_01_download_excel_report(self):
        """Test the Excel report download controller endpoint."""
        # Create a test user with the required group
        user = self.env['res.users'].create({
            'name': 'Test Export User',
            'login': 'test_export_user',
            'password': 'testpassword',
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('product_export_with_images.group_product_export_with_images').id
            ])]
        })
        
        product_tmpl = self.env['product.template'].create({
            'name': 'Test Controller Template',
            'list_price': 200.0,
        })
        
        # Create the wizard AS the test user so they own the transient record
        wizard = self.env['product.export'].with_user(user).create({
            'product_tmp_ids': [(6, 0, product_tmpl.ids)]
        })
        
        url = f"/products_download/excel_report/{wizard.id}"
        
        # Authenticate as the newly created user
        self.authenticate('test_export_user', 'testpassword')
        response = self.url_open(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get('Content-Type'),
            'application/vnd.ms-excel'
        )
        self.assertIn('attachment', response.headers.get('Content-Disposition', ''))
        self.assertIn('Products.xlsx', response.headers.get('Content-Disposition', ''))
