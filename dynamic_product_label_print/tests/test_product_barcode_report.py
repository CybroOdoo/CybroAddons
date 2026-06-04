from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.dynamic_product_label_print.report.product_barcode_report import _prepare_datas


@tagged('post_install', '-at_install')
class TestProductBarcodeReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Dynamic Label Product',
            'barcode': '1234567890123',
            'list_price': 42.0,
        })

    def test_prepare_datas_for_product_product(self):
        data = {
            'active_model': 'product.product',
            'quantity_by_product': {self.product.id: 3},
        }

        result = _prepare_datas(self.env, data)

        quantity_by_product = result['quantity']
        self.assertEqual(list(quantity_by_product), [self.product])
        self.assertEqual(quantity_by_product[self.product], [(
            self.product.barcode,
            3,
            self.product.name,
            self.product.categ_id.name,
            self.product.type,
            self.product.list_price,
        )])

    def test_prepare_datas_for_product_template_with_custom_barcodes(self):
        data = {
            'active_model': 'product.template',
            'quantity_by_product': {self.product.product_tmpl_id.id: 1},
            'custom_barcodes': {
                self.product.product_tmpl_id.id: [('LOT-001', 2)],
            },
        }

        result = _prepare_datas(self.env, data)

        quantity_by_product = result['quantity']
        self.assertEqual(list(quantity_by_product), [self.product.product_tmpl_id])
        self.assertIn(('LOT-001', 2), quantity_by_product[self.product.product_tmpl_id])

    def test_prepare_datas_rejects_unknown_active_model(self):
        with self.assertRaises(UserError):
            _prepare_datas(self.env(context=dict(self.env.context, lang='en_US')), {
                'active_model': 'res.partner',
                'quantity_by_product': {},
            })

    def test_get_report_values_uses_prepare_datas(self):
        report = self.env['report.dynamic_product_label_print.report_dynamic']
        data = {
            'active_model': 'product.product',
            'quantity_by_product': {self.product.id: 2},
        }

        result = report._get_report_values([], data)

        self.assertIn(self.product, result['quantity'])
