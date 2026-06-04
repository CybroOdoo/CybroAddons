from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):

    def test_source_location_is_saved_as_config_parameter(self):
        location = self.env['stock.location'].create({
            'name': 'POS Source Location',
            'usage': 'internal',
        })
        settings = self.env['res.config.settings'].create({
            'source_loc_id': location.id,
        })

        settings.set_values()

        source_loc_id = self.env['ir.config_parameter'].sudo().get_param(
            'pos_load_products_location.source_loc_id'
        )
        self.assertEqual(source_loc_id, str(location.id))

    def test_source_location_field_accepts_only_internal_locations(self):
        field = self.env['res.config.settings']._fields['source_loc_id']

        self.assertEqual(field.domain, "[('usage','=','internal')]")
