from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestEventBilling(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Event Customer',
            'email': 'customer@eventtest.com',
        })
        cls.other_partner = cls.env['res.partner'].create({
            'name': 'Other Event Customer',
            'email': 'other@eventtest.com',
        })
        cls.container_type = cls.env['wm.container.type'].create({
            'name': 'Standard 1100L Bin',
            'capacity_weight': 500.0,
        })
        cls.collection_point = cls.env['wm.collection.point'].create({
            'name': 'Test Site A',
            'partner_id': cls.partner.id,
            'container_id': cls.container_type.id,
        })
        cls.waste_category = cls.env['wm.waste.category'].create({
            'name': 'General Waste TestEventBilling',
            'code': 'GW01',
            'price': 0.15,
        })

        # 1. Create General & Partner Pricing Rules
        cls.general_extra_rule = cls.env['wm.event.pricing.rule'].create({
            'name': 'General Extra Pickup',
            'event_type': 'extra_pickup',
            'partner_id': False,
            'price_unit': 75.0,
            'sequence': 10,
        })
        cls.partner_extra_rule = cls.env['wm.event.pricing.rule'].create({
            'name': 'Special Extra Pickup',
            'event_type': 'extra_pickup',
            'partner_id': cls.partner.id,
            'price_unit': 60.0,
            'sequence': 5,
        })
        cls.general_overweight_rule = cls.env['wm.event.pricing.rule'].create({
            'name': 'General Overweight Fee',
            'event_type': 'overweight',
            'partner_id': False,
            'price_unit': 0.25,  # per kg excess
            'sequence': 10,
        })
        cls.general_contamination_rule = cls.env['wm.event.pricing.rule'].create({
            'name': 'General Contamination Fee',
            'event_type': 'contamination',
            'partner_id': False,
            'price_unit': 150.0,
            'sequence': 10,
        })

    def test_01_precedence_and_extra_pickup_hook(self):
        """Test rate precedence (customer rule > general rule) and extra_pickup auto-creation."""
        # Service request for partner
        req = self.env['wm.portal.service.request'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.collection_point.id,
            'request_type': 'extra_pickup',
            'requested_date': fields.Date.today(),
        })
        req.action_submit()
        req.action_approve()

        self.assertTrue(req.collection_order_id)
        event = self.env['wm.billable.event'].search([('portal_request_id', '=', req.id)], limit=1)
        self.assertTrue(event)
        self.assertEqual(event.event_type, 'extra_pickup')
        # Customer-specific rate (60.0) should beat general rate (75.0)
        self.assertEqual(event.price_unit, 60.0)

        # Service request for other partner without specific rule -> should get general rule (75.0)
        other_point = self.env['wm.collection.point'].create({
            'name': 'Other Site',
            'partner_id': self.other_partner.id,
        })
        other_req = self.env['wm.portal.service.request'].create({
            'partner_id': self.other_partner.id,
            'collection_point_id': other_point.id,
            'request_type': 'extra_pickup',
            'requested_date': fields.Date.today(),
        })
        other_req.action_submit()
        other_req.action_approve()
        other_event = self.env['wm.billable.event'].search([('portal_request_id', '=', other_req.id)], limit=1)
        self.assertTrue(other_event)
        self.assertEqual(other_event.price_unit, 75.0)

    def test_02_overweight_auto_detection(self):
        """Test overweight load detection when confirmed weight exceeds container capacity."""
        # Create route, vehicle, driver for order completion
        route = self.env['wm.route'].create({
            'name': 'Test Event Route',
            'state': 'running',
        })
        order = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.collection_point.id,
            'route_id': route.id,
            'state': 'in_progress',
            'order_line_ids': [(0, 0, {
                'category_id': self.waste_category.id,
                'weight': 650.0,  # Capacity is 500.0 kg -> 150 kg excess
            })]
        })
        order.action_complete()
        self.assertEqual(order.state, 'completed')

        # Check overweight billable event
        event = self.env['wm.billable.event'].search([
            ('collection_order_id', '=', order.id),
            ('event_type', '=', 'overweight')
        ], limit=1)
        self.assertTrue(event)
        self.assertEqual(event.quantity, 150.0)
        self.assertEqual(event.price_unit, 0.25)
        self.assertEqual(event.amount, 37.50)

    def test_03_contamination_auto_detection(self):
        """Test contamination billable event creation upon inspection failure."""
        # The customer is taken from the batch's collection order
        order = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.collection_point.id,
            'state': 'completed',
            'order_line_ids': [(0, 0, {
                'category_id': self.waste_category.id,
                'weight': 300.0,
            })]
        })
        batch = self.env['waste.batch'].create({
            'name': 'Batch-Contam-01',
            'collection_order_id': order.id,
        })
        inspection = self.env['wm.batch.inspection'].create({
            'batch_id': batch.id,
            'contamination_percentage': 45.0,
        })
        inspection.action_fail_inspection()

        event = self.env['wm.billable.event'].search([
            ('notes', 'ilike', inspection.name),
            ('event_type', '=', 'contamination')
        ], limit=1)
        self.assertTrue(event)
        self.assertEqual(event.price_unit, 150.0)
        self.assertEqual(event.partner_id, self.partner)

    def test_04_consolidated_invoicing(self):
        """Test pulling confirmed billable events into consolidated invoice."""
        # Create a confirmed event
        event = self.env['wm.billable.event'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.collection_point.id,
            'event_type': 'emergency_callout',
            'event_date': fields.Date.today(),
            'quantity': 1.0,
            'price_unit': 200.0,
            'state': 'confirmed',
        })

        # Create a completed order
        order = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.collection_point.id,
            'state': 'completed',
            'order_line_ids': [(0, 0, {
                'category_id': self.waste_category.id,
                'weight': 100.0,
            })]
        })

        consolidated = self.env['wm.consolidated.invoice'].create({
            'partner_id': self.partner.id,
            'date_from': fields.Date.today().replace(day=1),
            'date_to': fields.Date.today(),
            'order_ids': [(6, 0, [order.id])],
        })

        consolidated.action_generate_invoice()

        self.assertEqual(consolidated.state, 'invoiced')
        self.assertTrue(consolidated.invoice_id)
        self.assertEqual(event.state, 'invoiced')
