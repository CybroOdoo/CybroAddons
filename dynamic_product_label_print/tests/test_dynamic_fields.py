from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDynamicFields(TransactionCase):

    def test_set_domain_limits_fields_to_product_product_base_fields(self):
        product_model = self.env['ir.model'].search([
            ('model', '=', 'product.product'),
        ], limit=1)

        domain = self.env['dynamic.fields'].set_domain()

        self.assertEqual(domain, [
            ('model_id', '=', product_model.id),
            ('state', '=', 'base'),
            ('name', '=', ['name', 'categ_id', 'type', 'list_price']),
        ])

    def test_type_is_related_to_selected_field_type(self):
        name_field = self.env['ir.model.fields'].search([
            ('model', '=', 'product.product'),
            ('name', '=', 'name'),
        ], limit=1)
        dynamic_field = self.env['dynamic.fields'].create({
            'fd_name_id': name_field.id,
            'size': '14',
            'color': '#000000',
        })

        self.assertEqual(dynamic_field.type, name_field.ttype)
