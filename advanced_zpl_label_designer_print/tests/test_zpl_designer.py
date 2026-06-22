# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestZplDesigner(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestZplDesigner, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Create a product
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'default_code': 'TEST-001',
            'barcode': '123456789012',
            'list_price': 100.0,
            'weight': 1.5,
        })
        
        cls.product_model = cls.env['ir.model'].search([('model', '=', 'product.product')], limit=1)
        cls.field_name = cls.env['ir.model.fields'].search([('model_id', '=', cls.product_model.id), ('name', '=', 'name')], limit=1)
        
        # Create ZPL Template
        cls.template = cls.env['zpl.label.template'].create({
            'name': 'Test Label Template',
            'model_id': cls.product_model.id,
            'width': 100,
            'height': 150,
            'unit': 'mm',
            'dpi': '203',
        })
        
        # Create Elements
        cls.el_text = cls.env['zpl.label.element'].create({
            'template_id': cls.template.id,
            'name': 'Product Name',
            'type': 'text',
            'field_id': cls.field_name.id,
            'x_pos': 10,
            'y_pos': 10,
            'font_size': 30,
        })
        
        cls.el_price = cls.env['zpl.label.element'].create({
            'template_id': cls.template.id,
            'name': 'Price',
            'type': 'text',
            'x_pos': 10,
            'y_pos': 50,
            'data_format': 'Price: {{value}}',
        })
        
        cls.el_barcode = cls.env['zpl.label.element'].create({
            'template_id': cls.template.id,
            'name': 'Barcode',
            'type': 'barcode',
            'barcode_type': 'code128',
            'x_pos': 10,
            'y_pos': 100,
        })
        
        cls.el_qrcode = cls.env['zpl.label.element'].create({
            'template_id': cls.template.id,
            'name': 'QRCode',
            'type': 'qrcode',
            'x_pos': 10,
            'y_pos': 150,
            'width': 100,
        })

        cls.el_rect = cls.env['zpl.label.element'].create({
            'template_id': cls.template.id,
            'name': 'Rectangle',
            'type': 'rect',
            'x_pos': 5,
            'y_pos': 5,
            'width': 200,
            'height': 200,
        })

        cls.el_line = cls.env['zpl.label.element'].create({
            'template_id': cls.template.id,
            'name': 'Line',
            'type': 'line',
            'x_pos': 5,
            'y_pos': 210,
            'width': 200,
            'height': 2,
        })
        
        cls.el_image = cls.env['zpl.label.element'].create({
            'template_id': cls.template.id,
            'name': 'logo.png',
            'type': 'image',
            'x_pos': 5,
            'y_pos': 220,
        })


    def test_01_template_zpl_generation(self):
        """Test ZPL content generation logic."""
        zpl_with_record = self.template.generate_zpl_for_product(self.product)
        
        self.assertIn('^XA', zpl_with_record)
        self.assertIn('^XZ', zpl_with_record)
        
        # Check text field mapping (name)
        self.assertIn('^FDTest Product^FS', zpl_with_record)
        
        # Check fallback text logic with data format (Price)
        self.assertIn('Price: 100.00', zpl_with_record)
        
        # Check barcode mapping (fallback from name contains barcode)
        self.assertIn('123456789012', zpl_with_record)
        self.assertIn('^BC', zpl_with_record) # code128
        
        # Check qrcode
        self.assertIn('^BQN', zpl_with_record)
        self.assertIn('^FDQA,QRCode^FS', zpl_with_record)

        # Check rect
        self.assertIn('^GB', zpl_with_record)

        # Check image
        self.assertIn('^FD[IMAGE: logo.png]^FS', zpl_with_record)


    def test_02_save_design_from_js(self):
        """Test updating template elements from JS JSON."""
        elements_data = [
            {
                'name': 'New Text',
                'type': 'text',
                'x_pos': 20,
                'y_pos': 20,
                'width': 100,
                'height': 50,
                'font_size': 25,
            }
        ]
        res = self.env['zpl.label.template'].save_design_from_js(self.template.id, elements_data)
        self.assertTrue(res)
        
        self.assertEqual(len(self.template.element_ids), 1)
        self.assertEqual(self.template.element_ids.name, 'New Text')
        self.assertEqual(self.template.element_ids.font_size, 25)
        
        # also check compute
        self.assertTrue(self.template.zpl_content)
        self.assertIn('New Text', self.template.zpl_content)


    def test_03_action_preview(self):
        """Test action_preview returns correctly."""
        action = self.template.action_preview()
        if action.get('type') == 'ir.actions.act_window' and action.get('res_model') == 'base.document.layout':
            action = action.get('context', {}).get('report_action', action)
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_name'), 'advanced_zpl_label_designer_print.report_zpl_view')


    def test_04_product_label_layout(self):
        """Test print processing from product.label.layout wizard."""
        # Create layout wizard
        wizard = self.env['product.label.layout'].with_context(
            active_model='product.product',
            active_ids=self.product.ids
        ).create({
            'print_format': 'advanced_zpl_label_designer_print',
            'zpl_template_id': self.template.id,
            'custom_quantity': 2,
        })
        
        action = wizard.process()
        if action.get('type') == 'ir.actions.act_window' and action.get('res_model') == 'base.document.layout':
            action = action.get('context', {}).get('report_action', action)
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('data').get('zpl_template_id'), self.template.id)
        self.assertEqual(action.get('data').get('quantity'), 2)
        
        # Test validation error when no template is selected
        wizard.zpl_template_id = False
        with self.assertRaises(UserError):
            wizard.process()


    def test_05_ir_actions_report(self):
        """Test the custom _render_qweb_text for zpl_view report."""
        report = self.env.ref('advanced_zpl_label_designer_print.action_report_zpl_label_instance', raise_if_not_found=False)
        if report:
            content, ext = self.env['ir.actions.report']._render_qweb_text(
                'advanced_zpl_label_designer_print.report_zpl_view',
                res_ids=[self.template.id],
                data={
                    'zpl_template_id': self.template.id,
                    'product_ids': self.product.ids,
                    'quantity': 1,
                }
            )
            self.assertEqual(ext, 'txt')
            # It returns bytes, so check string conversion
            self.assertIn(b'^XA', content)
            self.assertIn(b'Test Product', content)
