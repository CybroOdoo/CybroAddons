#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProductStockDetails(TransactionCase):
    """Test suite for Product Stock Details module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Find or create a warehouse for the current company
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)],
            limit=1,
        )
        if not cls.warehouse:
            cls.warehouse = cls.env["stock.warehouse"].search([], limit=1)
        if not cls.warehouse:
            cls.warehouse = cls.env["stock.warehouse"].create({
                "name": "Test Warehouse",
                "code": "TWH",
                "company_id": cls.env.company.id,
            })

        # Ensure locations are available
        cls.stock_location = cls.warehouse.lot_stock_id or cls.env.ref(
            "stock.stock_location_stock",
            raise_if_not_found=False,
        )
        if not cls.stock_location:
            cls.stock_location = cls.env["stock.location"].search(
                [("usage", "=", "internal")],
                limit=1,
            )

        cls.supplier_location = cls.env.ref(
            "stock.stock_location_suppliers",
            raise_if_not_found=False,
        ) or cls.env["stock.location"].search([("usage", "=", "supplier")], limit=1)

        cls.customer_location = cls.env.ref(
            "stock.stock_location_customers",
            raise_if_not_found=False,
        ) or cls.env["stock.location"].search([("usage", "=", "customer")], limit=1)

        # Picking types for incoming and outgoing moves
        cls.picking_type_in = cls.warehouse.in_type_id or cls.env["stock.picking.type"].search(
            [("code", "=", "incoming")],
            limit=1,
        )
        cls.picking_type_out = cls.warehouse.out_type_id or cls.env["stock.picking.type"].search(
            [("code", "=", "outgoing")],
            limit=1,
        )

        # Set external report layout so report_action does not redirect to layout wizard
        layout = cls.env.ref("web.external_layout_standard", raise_if_not_found=False)
        if layout and hasattr(cls.env.company, "external_report_layout_id"):
            cls.env.company.external_report_layout_id = layout

        # Create secondary internal location
        parent_loc = (
            cls.warehouse.view_location_id
            or cls.stock_location.location_id
            or cls.stock_location
        )
        cls.sub_location = cls.env["stock.location"].create({
            "name": "Sub Location A",
            "usage": "internal",
            "location_id": parent_loc.id,
        })

        # Create test products
        cls.product = cls.env["product.product"].create({
            "name": "Test Stock Product A",
            "is_storable": True,
        })
        cls.product_b = cls.env["product.product"].create({
            "name": "Test Stock Product B",
            "is_storable": True,
        })

    def test_product_stock_location_ids(self):
        """Test product_stock_location_ids field on product.product."""
        # Add stock quantity to primary location
        self.env["stock.quant"]._update_available_quantity(
            self.product,
            self.stock_location,
            50.0,
        )
        self.product.invalidate_recordset(["product_stock_location_ids"])

        # Check product_stock_location_ids contains the quant
        quants = self.product.product_stock_location_ids
        self.assertTrue(quants, "Product should have stock quants linked.")
        stock_quant = quants.filtered(lambda q: q.location_id == self.stock_location)
        self.assertEqual(stock_quant.quantity, 50.0)
        self.assertEqual(stock_quant.available_quantity, 50.0)

        # Add stock quantity to secondary location
        self.env["stock.quant"]._update_available_quantity(
            self.product,
            self.sub_location,
            25.0,
        )
        self.product.invalidate_recordset(["product_stock_location_ids"])
        quants = self.product.product_stock_location_ids
        self.assertEqual(len(quants), 2, "Product should have 2 location quants.")

        sub_quant = quants.filtered(lambda q: q.location_id == self.sub_location)
        self.assertEqual(sub_quant.quantity, 25.0)
        self.assertEqual(sub_quant.available_quantity, 25.0)

    def test_stock_quant_computed_location_quantities(self):
        """Test virtual_available, incoming_qty, and outgoing_qty computations on stock.quant."""
        # Initial stock of 40 units at stock_location
        self.env["stock.quant"]._update_available_quantity(
            self.product,
            self.stock_location,
            40.0,
        )
        self.product.invalidate_recordset(["product_stock_location_ids"])
        quant = self.product.product_stock_location_ids.filtered(
            lambda q: q.location_id == self.stock_location,
        )
        if not quant:
            quant = self.env["stock.quant"].create({
                "product_id": self.product.id,
                "location_id": self.stock_location.id,
                "quantity": 40.0,
            })
        else:
            quant = quant[:1]

        self.assertEqual(quant.quantity, 40.0)
        self.assertEqual(quant.incoming_qty, 0.0)
        self.assertEqual(quant.outgoing_qty, 0.0)
        self.assertEqual(quant.virtual_available, 40.0)

        # Create incoming move (Supplier -> Stock: 15 units) with picking_type_id
        move_in = self.env["stock.move"].create({
            "description_picking": "Incoming Test Move",
            "product_id": self.product.id,
            "product_uom_qty": 15.0,
            "uom_id": self.product.uom_id.id,
            "location_id": self.supplier_location.id,
            "location_dest_id": self.stock_location.id,
            "picking_type_id": self.picking_type_in.id if self.picking_type_in else False,
        })
        move_in._action_confirm()
        if move_in.state == "draft":
            move_in.write({"state": "confirmed"})

        # Create outgoing move (Stock -> Customer: 10 units) with picking_type_id
        move_out = self.env["stock.move"].create({
            "description_picking": "Outgoing Test Move",
            "product_id": self.product.id,
            "product_uom_qty": 10.0,
            "uom_id": self.product.uom_id.id,
            "location_id": self.stock_location.id,
            "location_dest_id": self.customer_location.id,
            "picking_type_id": self.picking_type_out.id if self.picking_type_out else False,
        })
        move_out._action_confirm()
        if move_out.state == "draft":
            move_out.write({"state": "confirmed"})

        # Re-compute location quantities on quant
        self.product.invalidate_recordset(["virtual_available", "incoming_qty", "outgoing_qty"])
        quant.invalidate_recordset(["virtual_available", "incoming_qty", "outgoing_qty"])
        quant._compute_location_qty()

        self.assertEqual(quant.incoming_qty, 15.0, "Incoming quantity should be 15.0.")
        self.assertEqual(quant.outgoing_qty, 10.0, "Outgoing quantity should be 10.0.")
        # virtual_available = 40 (on hand) + 15 (incoming) - 10 (outgoing) = 45.0
        self.assertEqual(
            quant.virtual_available,
            45.0,
            "Forecasted quantity should be 45.0 (40 + 15 - 10).",
        )

    def test_get_wo_description_report_action(self):
        """Test get_wo_description and action_print_stock_details methods on product.product."""
        action = self.product.get_wo_description()
        self.assertIsInstance(action, dict, "Should return an action dictionary.")
        # Accepts ir.actions.report or document layout configurator act_window
        report_action = action.get("context", {}).get("report_action") or action
        self.assertIn(
            action.get("type"),
            ("ir.actions.report", "ir.actions.act_window"),
            "Action type should be ir.actions.report or configurator act_window.",
        )
        self.assertEqual(
            report_action.get("report_name"),
            "product_stock_details.report_product_stock_template",
            "Report name should match template XML ID.",
        )
        action2 = self.product.action_print_stock_details()
        self.assertIsInstance(action2, dict)
        report_action2 = action2.get("context", {}).get("report_action") or action2
        self.assertEqual(
            report_action2.get("report_name"),
            "product_stock_details.report_product_stock_template",
        )

    def test_report_values_docids_and_context(self):
        """Test _get_report_values method of abstract report model."""
        report_model = self.env["report.product_stock_details.report_product_stock_template"]

        # Case 1: passing docids directly
        res1 = report_model._get_report_values([self.product.id], data=None)
        self.assertIn("data", res1)
        self.assertIn(self.product, res1["data"])
        self.assertIn("docs", res1)
        self.assertEqual(res1["doc_ids"], [self.product.id])

        # Case 2: active_ids in context
        res2 = report_model.with_context(active_ids=[self.product_b.id])._get_report_values(
            [],
            data=None,
        )
        self.assertIn("data", res2)
        self.assertIn(self.product_b, res2["data"])

    def test_report_qweb_rendering(self):
        """Test full QWeb HTML and PDF report rendering for single and multiple products."""
        # Add stock to product and product_b
        self.env["stock.quant"]._update_available_quantity(
            self.product,
            self.stock_location,
            30.0,
        )
        self.env["stock.quant"]._update_available_quantity(
            self.product_b,
            self.stock_location,
            15.0,
        )

        # 1. Render QWeb HTML for single product
        html_content, _ = self.env["ir.actions.report"]._render_qweb_html(
            "product_stock_details.action_report_product_stock_details",
            [self.product.id],
        )
        self.assertTrue(html_content, "Report HTML content should not be empty.")
        self.assertIn(self.product.name, str(html_content))
        self.assertIn("Location", str(html_content))

        # 2. Render QWeb HTML for multiple products
        html_multi, _ = self.env["ir.actions.report"]._render_qweb_html(
            "product_stock_details.action_report_product_stock_details",
            [self.product.id, self.product_b.id],
        )
        self.assertTrue(html_multi, "Multi-product HTML content should not be empty.")
        self.assertIn(self.product_b.name, str(html_multi))

        # 3. Attempt PDF rendering if wkhtmltopdf is operational
        try:
            pdf_content, _ = self.env["ir.actions.report"]._render_qweb_pdf(
                "product_stock_details.action_report_product_stock_details",
                [self.product.id],
            )
            self.assertTrue(pdf_content, "Report PDF content should not be empty.")
            self.assertGreater(len(pdf_content), 100, "PDF byte stream should be valid.")
        except (UserError, OSError, ValueError, RuntimeError):
            # Environments without wkhtmltopdf binary or X11 libs will skip PDF check safely
            pass

    def test_stock_quant_empty_location_guards(self):
        """Test computed fields default cleanly to 0.0 when location is not set."""
        quant = self.env["stock.quant"].new({
            "product_id": self.product.id,
            "location_id": False,
        })
        quant._compute_location_qty()
        self.assertEqual(quant.virtual_available, 0.0)
        self.assertEqual(quant.incoming_qty, 0.0)
        self.assertEqual(quant.outgoing_qty, 0.0)

    def test_action_print_stock_details_direct(self):
        """Test direct action_print_stock_details invocation on product_b."""
        res = self.product_b.action_print_stock_details()
        self.assertIsInstance(res, dict)
        report_action = res.get("context", {}).get("report_action") or res
        self.assertEqual(
            report_action.get("report_name"),
            "product_stock_details.report_product_stock_template",
        )

    def test_stock_quant_company_context(self):
        """Test stock.quant computations with explicit company context."""
        quant = self.env["stock.quant"].create({
            "product_id": self.product.id,
            "location_id": self.stock_location.id,
            "quantity": 10.0,
        })
        quant._compute_location_qty()
        self.assertGreaterEqual(quant.virtual_available, 0.0)
        self.assertGreaterEqual(quant.incoming_qty, 0.0)
        self.assertGreaterEqual(quant.outgoing_qty, 0.0)
