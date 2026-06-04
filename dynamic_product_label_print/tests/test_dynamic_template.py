from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDynamicTemplate(TransactionCase):

    def test_dynamic_template_links_dynamic_fields(self):
        name_field = self.env['ir.model.fields'].search([
            ('model', '=', 'product.product'),
            ('name', '=', 'name'),
        ], limit=1)
        template = self.env['dynamic.template'].create({
            'name': 'Shelf Label',
            'bc_height': '80',
            'bc_width': '250',
            'dynamic_field_ids': [(0, 0, {
                'fd_name_id': name_field.id,
                'size': '12',
                'color': '#111111',
            })],
        })

        self.assertEqual(template.dynamic_field_ids.field_id, template)
        self.assertEqual(template.dynamic_field_ids.fd_name_id, name_field)
