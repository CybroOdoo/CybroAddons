from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('-at_install', 'post_install')
class TestPosConfig(TransactionCase):

    def test_partial_payment_is_enabled_by_default(self):
        config = self.env['pos.config'].create({'name': 'Partial Payment POS'})

        self.assertTrue(config.partial_payment)

    def test_partial_payment_can_be_disabled(self):
        config = self.env['pos.config'].create({
            'name': 'No Partial Payment POS',
            'partial_payment': False,
        })

        self.assertFalse(config.partial_payment)
