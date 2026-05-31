from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('-at_install', 'post_install')
class TestResPartner(TransactionCase):

    def test_prevent_partial_payment_field_can_be_enabled(self):
        partner = self.env['res.partner'].create({
            'name': 'Prevent Partial Payment Customer',
            'prevent_partial_payment': True,
        })

        self.assertTrue(partner.prevent_partial_payment)

    def test_load_pos_data_fields_adds_prevent_partial_payment(self):
        fields = self.env['res.partner']._load_pos_data_fields(config_id=False)

        self.assertIn('prevent_partial_payment', fields)
