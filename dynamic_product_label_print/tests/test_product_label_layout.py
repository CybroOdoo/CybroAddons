from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProductLabelLayout(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.name_field = cls.env['ir.model.fields'].search([
            ('model', '=', 'product.product'),
            ('name', '=', 'name'),
        ], limit=1)
        cls.list_price_field = cls.env['ir.model.fields'].search([
            ('model', '=', 'product.product'),
            ('name', '=', 'list_price'),
        ], limit=1)
        cls.template = cls.env['dynamic.template'].create({
            'name': 'Dynamic Label',
            'bc_height': '90',
            'bc_width': '300',
            'dynamic_field_ids': [
                (0, 0, {
                    'fd_name_id': cls.name_field.id,
                    'size': '16',
                    'color': '#000000',
                }),
                (0, 0, {
                    'fd_name_id': cls.list_price_field.id,
                    'size': '12',
                    'color': '#333333',
                }),
            ],
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Wizard Label Product',
            'barcode': '9876543210987',
            'list_price': 25.0,
        })

    def _create_wizard(self, values=None):
        vals = {
            'print_format': 'dynamic_template',
            'custom_quantity': 4,
            'dynamic_template_id': self.template.id,
            'product_ids': [(6, 0, self.product.ids)],
        }
        if values:
            vals.update(values)
        return self.env['product.label.layout'].create(vals)

    def test_onchange_dynamic_template_id_copies_template_fields(self):
        wizard = self._create_wizard()

        wizard._onchange_dynamic_template_id()

        self.assertEqual(wizard.dynamic_field_ids, self.template.dynamic_field_ids)

    def test_prepare_report_data_for_dynamic_product_labels(self):
        wizard = self._create_wizard()
        wizard._onchange_dynamic_template_id()

        xml_id, data = wizard._prepare_report_data()

        self.assertEqual(xml_id, 'dynamic_product_label_print.product_label_layout_form_dynamic')
        self.assertEqual(data['active_model'], 'product.product')
        self.assertEqual(data['quantity_by_product'], {self.product.id: 4})
        self.assertEqual(data['layout_wizard'], self.template)
        self.assertEqual(data['bc_width'], self.template.bc_width)
        self.assertEqual(data['bc_height'], self.template.bc_height)
        self.assertEqual(len(data['dynamic_field_ids'][0]), 2)

    def test_prepare_report_data_for_dynamic_template_labels(self):
        wizard = self._create_wizard({
            'product_ids': [(5, 0, 0)],
            'product_tmpl_ids': [(6, 0, self.product.product_tmpl_id.ids)],
        })
        wizard._onchange_dynamic_template_id()

        xml_id, data = wizard._prepare_report_data()

        self.assertEqual(xml_id, 'dynamic_product_label_print.product_label_layout_form_dynamic')
        self.assertEqual(data['active_model'], 'product.template')
        self.assertEqual(data['quantity_by_product'], {self.product.product_tmpl_id.id: 4})

    def test_process_returns_dynamic_report_action(self):
        wizard = self._create_wizard()
        wizard._onchange_dynamic_template_id()
        captured = {}

        def _fake_report_action(report_self, docids, data=None, config=True):
            captured['docids'] = docids
            captured['data'] = data
            captured['config'] = config
            return {'type': 'ir.actions.report'}

        self.patch(type(self.env['ir.actions.report']), 'report_action', _fake_report_action)

        action = wizard.process()

        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertTrue(action['close_on_report_download'])
        self.assertIsNone(captured['docids'])
        self.assertEqual(captured['data']['quantity_by_product'], {self.product.id: 4})
