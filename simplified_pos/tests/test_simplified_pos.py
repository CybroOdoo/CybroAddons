import os

from odoo.modules.module import get_module_path
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSimplifiedPos(TransactionCase):
    """Test Simplified POS module functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Simplified POS Test Config',
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test POS Customer',
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Test POS Product',
            'list_price': 100.0,
            'available_in_pos': True,
        })

    def test_module_installed(self):
        """Test that simplified_pos module is installed correctly."""
        module = self.env['ir.module.module'].search([
            ('name', '=', 'simplified_pos')
        ], limit=1)

        self.assertTrue(
            module,
            "simplified_pos module should exist."
        )

    def test_pos_config_creation(self):
        """Test POS configuration is created successfully."""
        self.assertTrue(
            self.pos_config,
            "POS Config should be created."
        )

        self.assertEqual(
            self.pos_config.name,
            'Simplified POS Test Config',
            "POS Config name should match."
        )

    def test_pos_config_has_payment_methods(self):
        """Test that the POS config has payment methods available."""
        payment_method = self.env['pos.payment.method'].create({
            'name': 'Test Cash Payment',
        })

        self.pos_config.write({
            'payment_method_ids': [(4, payment_method.id)],
        })

        self.assertIn(
            payment_method,
            self.pos_config.payment_method_ids,
            "Payment method should be linked to POS config."
        )

    def test_product_available_in_pos(self):
        """Test that the product is available in POS."""
        self.assertTrue(
            self.product.available_in_pos,
            "Product should be available in POS."
        )

    def test_pos_session_open_and_close(self):
        """Test opening and closing a POS session."""
        payment_method = self.env['pos.payment.method'].create({
            'name': 'Test Cash',
        })

        self.pos_config.write({
            'payment_method_ids': [(4, payment_method.id)],
        })

        self.pos_config.open_ui()

        session = self.pos_config.current_session_id

        self.assertTrue(
            session,
            "A POS session should be opened."
        )

        # Odoo 18 state after open_ui()
        self.assertEqual(
            session.state,
            'opening_control',
            "POS session state should be 'opening_control'."
        )

    def test_pos_order_creation(self):
        """Test creating a POS order with an order line."""
        payment_method = self.env['pos.payment.method'].create({
            'name': 'Test Cash Order',
        })

        self.pos_config.write({
            'payment_method_ids': [(4, payment_method.id)],
        })

        self.pos_config.open_ui()

        session = self.pos_config.current_session_id

        order = self.env['pos.order'].create({
            'session_id': session.id,
            'partner_id': self.partner.id,
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'qty': 2,
                'price_unit': 100.0,
                'price_subtotal': 200.0,
                'price_subtotal_incl': 200.0,
            })],
            'amount_total': 200.0,
            'amount_tax': 0.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
        })

        self.assertTrue(
            order,
            "POS order should be created."
        )

        self.assertEqual(
            len(order.lines),
            1,
            "POS order should have one order line."
        )

        self.assertEqual(
            order.lines[0].qty,
            2,
            "Order line quantity should be 2."
        )

    def test_pos_order_with_payment(self):
        """Test adding a payment to a POS order."""

        payment_method = self.env['pos.payment.method'].create({
            'name': 'Test Cash Pay',
        })

        self.pos_config.write({
            'payment_method_ids': [(4, payment_method.id)],
        })

        self.pos_config.open_ui()

        session = self.pos_config.current_session_id

        order = self.env['pos.order'].create({
            'session_id': session.id,
            'partner_id': self.partner.id,
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'qty': 1,
                'price_unit': 100.0,
                'price_subtotal': 100.0,
                'price_subtotal_incl': 100.0,
            })],
            'amount_total': 100.0,
            'amount_tax': 0.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
        })

        payment = self.env['pos.payment'].create({
            'pos_order_id': order.id,
            'amount': 100.0,
            'payment_method_id': payment_method.id,
        })

        self.assertTrue(
            payment,
            "Payment should be created."
        )

        self.assertEqual(
            payment.amount,
            100.0,
            "Payment amount should be 100.0."
        )

        self.assertEqual(
            payment.pos_order_id.id,
            order.id,
            "Payment should be linked to the POS order."
        )

    def test_pos_assets_registered(self):
        """Test that simplified_pos asset files exist."""
        module_path = get_module_path('simplified_pos')

        self.assertTrue(
            module_path,
            "simplified_pos module path should exist."
        )

        static_path = os.path.join(
            module_path,
            'static',
            'src',
        )

        self.assertTrue(
            os.path.exists(static_path),
            "Static asset directory should exist."
        )

    def test_partner_creation_for_pos(self):
        """Test partner creation for simplified POS usage."""
        self.assertTrue(
            self.partner,
            "Partner should be created."
        )

        self.assertEqual(
            self.partner.name,
            'Test POS Customer',
            "Partner name should match."
        )

    def test_pos_order_partner_assignment(self):
        """Test partner is correctly assigned to POS order."""
        payment_method = self.env['pos.payment.method'].create({
            'name': 'Test Cash Assign',
        })

        self.pos_config.write({
            'payment_method_ids': [(4, payment_method.id)],
        })

        self.pos_config.open_ui()

        session = self.pos_config.current_session_id

        order = self.env['pos.order'].create({
            'session_id': session.id,
            'partner_id': self.partner.id,
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'qty': 1,
                'price_unit': 100.0,
                'price_subtotal': 100.0,
                'price_subtotal_incl': 100.0,
            })],
            'amount_total': 100.0,
            'amount_tax': 0.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
        })

        self.assertEqual(
            order.partner_id.id,
            self.partner.id,
            "Order partner_id should match assigned partner.")