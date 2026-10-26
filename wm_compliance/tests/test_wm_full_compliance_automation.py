from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestWmFullComplianceAutomation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.generator = cls.env['res.partner'].create({
            'name': 'Auto Compliance Generator Corp',
            'is_generator': True,
        })
        cls.transporter = cls.env['res.partner'].create({
            'name': 'Auto Compliance Logistics Ltd',
            'is_transporter': True,
        })
        cls.facility = cls.env['wm.disposal.facility'].create({
            'name': 'Auto Eco Disposal Plant',
        })
        cls.category = cls.env['wm.waste.category'].create({
            'name': 'Hazardous Chemical Stream',
            'code': 'HAZ-CHEM',
        })
        cls.collection_point = cls.env['wm.collection.point'].create({
            'name': 'Factory Site 1',
            'partner_id': cls.generator.id,
        })
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Volvo Fleet'})
        model = cls.env['fleet.vehicle.model'].create({'name': 'Waste Truck 101', 'brand_id': brand.id})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': model.id,
            'license_plate': 'WM-AUTO-101',
            'driver_id': cls.transporter.id,
        })

    def test_end_to_end_automated_compliance_pipeline(self):
        self.env['ir.config_parameter'].sudo().set_param('wm_collection.use_facility_gate_entry', 'True')
        # 1. Create Route and Collection Order
        route = self.env['wm.route'].create({
            'name': 'Test Compliance Route',
            'vehicle_id': self.vehicle.id,
            'driver_id': self.transporter.id,
        })
        order = self.env['wm.collection.order'].create({
            'partner_id': self.generator.id,
            'collection_point_id': self.collection_point.id,
            'route_id': route.id,
            'order_line_ids': [(0, 0, {
                'category_id': self.category.id,
                'weight': 1250.0,
            })],
        })

        # Complete collection order -> Triggers auto-manifest creation & collection
        order.action_complete()

        manifest = self.env['wm.compliance.manifest'].search([
            ('generator_id', '=', self.generator.id)
        ], limit=1)
        self.assertTrue(manifest, "Compliance Manifest should be automatically created upon order completion")
        self.assertEqual(manifest.state, 'collected', "Manifest should auto-advance to 'collected' state")
        self.assertEqual(manifest.total_quantity, 1250.0)

        # Check Gate Entry auto-created upon collection order completion in draft state
        gate_entry = self.env['wm.facility.gate.entry'].search([
            ('collection_order_id', '=', order.id)
        ], limit=1)
        self.assertTrue(gate_entry, "Gate Entry should be automatically created upon order completion")
        self.assertEqual(gate_entry.state, 'draft', "Gate Entry should be created in Draft state")

        # The weight received is confirmed at the gate
        gate_entry.write({'confirmed_weight': 2000.0})

        # Process reconciliation on scale intake
        gate_entry.action_process_reconciliation()

        # Check Manifest state -> Should auto-dispose
        self.assertEqual(manifest.state, 'disposed', "Manifest should auto-advance to 'disposed' state upon scale intake")

        # 3. Check Certificate of Destruction (COD) -> Should auto-generate and issue
        cert = self.env['wm.compliance.certificate'].search([
            ('manifest_id', '=', manifest.id)
        ], limit=1)
        self.assertTrue(cert, "Certificate of Destruction should be automatically generated upon manifest disposal")
        self.assertEqual(cert.state, 'issued', "Certificate of Destruction should auto-issue")
