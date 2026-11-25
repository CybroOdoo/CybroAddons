###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from unittest.mock import PropertyMock, patch
from urllib.parse import quote

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPosReturnBarcode(TransactionCase):
    """Test suite for pos_return_barcode module covering pos.order,
    res.config.settings, and pos.order.receipt barcode generation.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        cls.bank_journal = cls.env["account.journal"].search(
            [
                ("company_id", "=", cls.company.id),
                ("type", "=", "bank"),
            ],
            limit=1,
        )
        if not cls.bank_journal:
            cls.bank_journal = cls.env["account.journal"].create(
                {
                    "name": "POS Test Bank Journal",
                    "type": "bank",
                    "code": "PTB",
                    "company_id": cls.company.id,
                },
            )

        cls.payment_method = cls.env["pos.payment.method"].search(
            [
                ("company_id", "=", cls.company.id),
            ],
            limit=1,
        )
        if not cls.payment_method:
            cls.payment_method = cls.env["pos.payment.method"].create(
                {
                    "name": "POS Test Payment Method",
                    "type": "bank",
                    "journal_id": cls.bank_journal.id,
                    "company_id": cls.company.id,
                },
            )

        cls.pos_config = cls.env["pos.config"].create(
            {
                "name": "Test Return Barcode POS",
                "company_id": cls.company.id,
                "payment_method_ids": [(6, 0, cls.payment_method.ids)],
            },
        )

        cls.pos_session = cls.env["pos.session"].create(
            {
                "config_id": cls.pos_config.id,
                "user_id": cls.env.uid,
            },
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test POS Product",
                "list_price": 100.0,
                "available_in_pos": True,
            },
        )

        cls.pos_order = cls.env["pos.order"].create(
            {
                "company_id": cls.company.id,
                "session_id": cls.pos_session.id,
                "pos_reference": "Order 00042-001-0001",
                "lines": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "qty": 1,
                            "price_unit": 100.0,
                            "price_subtotal": 100.0,
                            "price_subtotal_incl": 100.0,
                        },
                    ),
                ],
                "amount_tax": 0.0,
                "amount_total": 100.0,
                "amount_paid": 100.0,
                "amount_return": 0.0,
            },
        )

    def test_pos_order_barcode_created(self):
        """Verify barcode is automatically populated from pos_reference on create."""
        self.assertEqual(
            self.pos_order.barcode,
            "000420010001",
            "Barcode should be stripped pos_reference without 'Order', spaces, or hyphens.",
        )
        self.assertFalse(
            self.pos_order.is_return,
            "Initial order should have is_return=False by default.",
        )

    def test_pos_order_batch_create(self):
        """Verify batch create correctly populates barcode for all orders."""
        orders = self.env["pos.order"].create([
            {
                "company_id": self.company.id,
                "session_id": self.pos_session.id,
                "pos_reference": "Order 00001-001-0001",
                "amount_tax": 0.0,
                "amount_total": 50.0,
                "amount_paid": 50.0,
                "amount_return": 0.0,
            },
            {
                "company_id": self.company.id,
                "session_id": self.pos_session.id,
                "pos_reference": "Order 00002-002-0002",
                "amount_tax": 0.0,
                "amount_total": 75.0,
                "amount_paid": 75.0,
                "amount_return": 0.0,
            },
        ])
        self.assertEqual(len(orders), 2)
        self.assertEqual(orders[0].barcode, "000010010001")
        self.assertEqual(orders[1].barcode, "000020020002")

    def test_action_barcode_return_success(self):
        """Verify action_barcode_return finds the order and returns its tracking number."""
        result = self.pos_order.action_barcode_return("000420010001")
        self.assertEqual(
            result,
            self.pos_order.tracking_number,
            "action_barcode_return should return tracking_number when matching unrefunded order exists.",
        )

    def test_action_barcode_return_not_found(self):
        """Verify action_barcode_return returns None when barcode does not match any order."""
        result = self.pos_order.action_barcode_return("NONEXISTENT_BARCODE")
        self.assertIsNone(
            result,
            "action_barcode_return should return None when order is not found.",
        )

    def test_action_barcode_return_already_refunded(self):
        """Verify action_barcode_return returns None if order already has refunds."""
        with patch.object(
            type(self.pos_order),
            "refund_orders_count",
            new_callable=PropertyMock,
            return_value=1,
        ):
            result = self.pos_order.action_barcode_return("000420010001")
            self.assertIsNone(
                result,
                "action_barcode_return should return None when refund_orders_count > 0.",
            )

    def test_prepare_refund_values(self):
        """Verify _prepare_refund_values sets is_return=True."""
        refund_values = self.pos_order._prepare_refund_values(self.pos_session)
        self.assertTrue(
            refund_values.get("is_return"),
            "_prepare_refund_values must include is_return=True.",
        )
        self.assertTrue(
            refund_values.get("is_refund"),
            "_prepare_refund_values must preserve standard is_refund flag.",
        )

    def test_res_config_settings_toggle(self):
        """Verify point_of_sale_barcode setting correctly writes to ir.config_parameter."""
        settings = self.env["res.config.settings"].create(
            {
                "point_of_sale_barcode": True,
            },
        )
        settings.execute()
        param_value = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_bool(
                "pos_return_barcode.receipt_barcode",
            )
        )
        self.assertTrue(
            param_value,
            "point_of_sale_barcode should set config parameter pos_return_barcode.receipt_barcode to True.",
        )

        settings = self.env["res.config.settings"].create(
            {
                "point_of_sale_barcode": False,
            },
        )
        settings.execute()
        param_value = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_bool(
                "pos_return_barcode.receipt_barcode",
            )
        )
        self.assertFalse(
            param_value,
            "point_of_sale_barcode should set config parameter pos_return_barcode.receipt_barcode to False.",
        )

    def test_receipt_generate_data_with_barcode(self):
        """Verify order_receipt_generate_data generates barcode image data URI when barcode is set."""
        data = self.pos_order.order_receipt_generate_data()
        self.assertIn("image", data)
        self.assertEqual(data["image"].get("pos_barcode"), "000420010001")
        self.assertTrue(
            data["image"]
            .get("pos_barcode_src", "")
            .startswith("data:image/png;base64,"),
            "pos_barcode_src should be a base64 encoded PNG data URI.",
        )

    def test_receipt_generate_data_fallback_reference(self):
        """Verify order_receipt_generate_data falls back to pos_reference when barcode is unset."""
        test_order = self.env["pos.order"].create(
            {
                "company_id": self.company.id,
                "session_id": self.pos_session.id,
                "pos_reference": "Order 00099-002-0002",
                "lines": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "qty": 1,
                            "price_unit": 50.0,
                            "price_subtotal": 50.0,
                            "price_subtotal_incl": 50.0,
                        },
                    ),
                ],
                "amount_tax": 0.0,
                "amount_total": 50.0,
                "amount_paid": 50.0,
                "amount_return": 0.0,
            },
        )
        with patch.object(
            type(test_order), "barcode", new_callable=PropertyMock, return_value=False,
        ):
            data = test_order.order_receipt_generate_data()
            self.assertEqual(
                data["image"].get("pos_barcode"),
                "000990020002",
                "Barcode should fall back to formatted pos_reference when barcode field is empty.",
            )
            self.assertTrue(
                data["image"]
                .get("pos_barcode_src", "")
                .startswith("data:image/png;base64,"),
                "Barcode image should be generated for fallback reference.",
            )

    def test_receipt_generate_data_exception_url_fallback(self):
        """Verify order_receipt_generate_data falls back to URL route on report barcode exception."""
        with patch.object(
            type(self.env["ir.actions.report"]),
            "barcode",
            side_effect=ValueError("Cannot convert into barcode."),
        ):
            data = self.pos_order.order_receipt_generate_data()
            expected_url = f"{self.pos_order.env.company.get_base_url()}/report/barcode/Code128/{quote(self.pos_order.barcode)}"
            self.assertEqual(
                data["image"].get("pos_barcode_src"),
                expected_url,
                "pos_barcode_src should fall back to barcode route URL when generation raises an exception.",
            )

    def test_receipt_generate_data_no_barcode_no_reference(self):
        """Verify order_receipt_generate_data skips barcode when neither barcode nor pos_reference exists."""
        test_order = self.env["pos.order"].create(
            {
                "company_id": self.company.id,
                "session_id": self.pos_session.id,
                "pos_reference": "Order 00055-001-0001",
                "lines": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "qty": 1,
                            "price_unit": 10.0,
                            "price_subtotal": 10.0,
                            "price_subtotal_incl": 10.0,
                        },
                    ),
                ],
                "amount_tax": 0.0,
                "amount_total": 10.0,
                "amount_paid": 10.0,
                "amount_return": 0.0,
            },
        )
        with (
            patch.object(
                type(test_order),
                "barcode",
                new_callable=PropertyMock,
                return_value=False,
            ),
            patch.object(
                type(test_order),
                "pos_reference",
                new_callable=PropertyMock,
                return_value=False,
            ),
        ):
            data = test_order.order_receipt_generate_data()
            self.assertNotIn(
                "pos_barcode",
                data["image"],
                "pos_barcode should not be in image dict when barcode and pos_reference are empty.",
            )

    def test_receipt_qweb_rendering_with_barcode(self):
        """Verify the inherited pos_order_receipt template renders the barcode image and text."""
        receipt_data = self.pos_order.order_receipt_generate_data()
        rendered_html = self.env["ir.qweb"]._render(
            "point_of_sale.pos_order_receipt", receipt_data,
        )
        self.assertIn(
            "pos-receipt-barcode",
            rendered_html,
            "Rendered receipt HTML must contain the pos-receipt-barcode image class.",
        )
        self.assertIn(
            self.pos_order.barcode,
            rendered_html,
            "Rendered receipt HTML must display the barcode value.",
        )
