# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import base64
from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import tagged, TransactionCase


@tagged('post_install', '-at_install', 'wm_security')
class TestWmSecurityRoles(TransactionCase):
    """
    Comprehensive End-to-End Test Suite verifying Role-Based Access Control (RBAC),
    record-level access rules, view rendering (get_views), button actions, and security
    barriers across all 8 Waste Management roles and unauthorized users.
    """

    @classmethod
    def setUpClass(cls):
        """ Set up test class fixtures and environment for all roles. """
        super().setUpClass()

        # 1. Driver / Field Collector
        cls.user_driver = cls.env['res.users'].create({
            'name': 'Test Driver User',
            'login': 'wm_driver_user',
            'email': 'driver@wm.test',
        })
        cls.env.ref('wm_base.group_wm_driver').write({'user_ids': [(4, cls.user_driver.id)]})

        # Another driver to test driver-to-driver isolation
        cls.user_other_driver = cls.env['res.users'].create({
            'name': 'Test Other Driver User',
            'login': 'wm_other_driver_user',
            'email': 'other_driver@wm.test',
        })
        cls.env.ref('wm_base.group_wm_driver').write({'user_ids': [(4, cls.user_other_driver.id)]})

        # 2. Dispatcher & Logistics
        cls.user_dispatcher = cls.env['res.users'].create({
            'name': 'Test Dispatcher User',
            'login': 'wm_dispatcher_user',
            'email': 'dispatcher@wm.test',
        })
        cls.env.ref('wm_base.group_wm_dispatcher').write({'user_ids': [(4, cls.user_dispatcher.id)]})

        # 3. Inventory & Yard Operator
        cls.user_inventory = cls.env['res.users'].create({
            'name': 'Test Yard Operator',
            'login': 'wm_yard_operator',
            'email': 'yard@wm.test',
        })
        cls.env.ref('wm_base.group_wm_inventory_operator').write({'user_ids': [(4, cls.user_inventory.id)]})

        # 4. Recycling Specialist
        cls.user_recycler = cls.env['res.users'].create({
            'name': 'Test Recycler Specialist',
            'login': 'wm_recycler_user',
            'email': 'recycler@wm.test',
        })
        cls.env.ref('wm_base.group_wm_recycler').write({'user_ids': [(4, cls.user_recycler.id)]})

        # 5. Billing & Finance
        cls.user_finance = cls.env['res.users'].create({
            'name': 'Test Finance User',
            'login': 'wm_finance_user',
            'email': 'finance@wm.test',
        })
        cls.env.ref('wm_base.group_wm_finance').write({'user_ids': [(4, cls.user_finance.id)]})

        # 6. Compliance Officer
        cls.user_compliance = cls.env['res.users'].create({
            'name': 'Test Compliance Officer',
            'login': 'wm_compliance_user',
            'email': 'compliance@wm.test',
        })
        cls.env.ref('wm_base.group_wm_compliance_officer').write({'user_ids': [(4, cls.user_compliance.id)]})

        # 7. Operations Manager
        cls.user_ops_mgr = cls.env['res.users'].create({
            'name': 'Test Operations Manager',
            'login': 'wm_ops_manager_user',
            'email': 'ops_mgr@wm.test',
        })
        cls.env.ref('wm_base.group_wm_ops_manager').write({'user_ids': [(4, cls.user_ops_mgr.id)]})

        # 8. Administrator
        cls.user_wm_admin = cls.env['res.users'].create({
            'name': 'Test WM Admin User',
            'login': 'wm_admin_role_user',
            'email': 'wm_admin@wm.test',
        })
        cls.env.ref('wm_base.group_wm_admin').write({'user_ids': [(4, cls.user_wm_admin.id)]})

        # 9. Unauthorized Base User (Internal user with no WM groups)
        cls.user_unauthorized = cls.env['res.users'].create({
            'name': 'Test Unauthorized Base User',
            'login': 'wm_unauthorized_user',
            'email': 'unauth@wm.test',
        })

        # Base shared test fixtures
        cls.partner = cls.env['res.partner'].create({
            'name': 'Security Test Partner',
            'email': 'partner@sec.test',
            'is_generator': True,
        })
        cls.category = cls.env['wm.waste.category'].create({
            'name': 'Sec Test Waste Cat',
            'code': 'SECCAT',
            'price': 15.0,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Sec Test Product',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category.id,
            'is_storable': True,
        })
        cls.warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.env.company.id)], limit=1)
        cls.location = cls.warehouse.lot_stock_id

        if 'wm.collection.point' in cls.env:
            cls.point = cls.env['wm.collection.point'].create({
                'name': 'Sec Test Point',
                'partner_id': cls.partner.id,
            })

    # =========================================================================
    # ROLE 1: DRIVER / FIELD COLLECTOR (group_wm_driver)
    # =========================================================================

    def test_01_driver_record_access_and_isolation(self):
        """Driver can read/write assigned orders but cannot delete them or modify unauthorized models."""
        if 'wm.collection.order' in self.env:
            order = self.env['wm.collection.order'].create({
                'partner_id': self.partner.id,
                'driver_id': self.user_driver.partner_id.id,
                'order_line_ids': [(0, 0, {
                    'category_id': self.category.id,
                    'weight': 20.0,
                })],
            })
            # Driver can read and write assigned order and order lines
            driver_order = self.env['wm.collection.order'].with_user(self.user_driver).browse(order.id)
            self.assertEqual(driver_order.name, order.name)
            driver_order.order_line_ids.write({'weight': 25.0})
            self.assertEqual(order.order_line_ids[0].weight, 25.0)

            # Driver CANNOT unlink collection order
            with self.assertRaises(AccessError):
                driver_order.unlink()

    def test_02_driver_views_and_button_actions(self):
        """Driver can load required views and execute collection order lifecycle and signing."""
        if 'wm.collection.order' in self.env:
            views = self.env['wm.collection.order'].with_user(self.user_driver).get_views(
                views=[(False, 'list'), (False, 'form')]
            )
            self.assertIn('list', views.get('views', {}))
            self.assertIn('form', views.get('views', {}))

            # Driver button actions: dispatch -> start -> complete
            order = self.env['wm.collection.order'].create({
                'partner_id': self.partner.id,
                'driver_id': self.user_driver.partner_id.id,
                'order_line_ids': [(0, 0, {
                    'category_id': self.category.id,
                    'weight': 50.0,
                })],
            })
            driver_order = self.env['wm.collection.order'].with_user(self.user_driver).browse(order.id)
            driver_order.write({'state': 'dispatched'})
            driver_order.action_start()
            self.assertEqual(driver_order.state, 'in_progress')
            driver_order.action_complete()
            self.assertEqual(driver_order.state, 'completed')

    def test_03_driver_security_barriers(self):
        """Driver is blocked from creating routes, pricing rules, billing runs, and facilities."""
        if 'wm.route' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.route'].with_user(self.user_driver).create({'name': 'Driver Forbidden Route'})

        if 'wm.pricing.rule' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.pricing.rule'].with_user(self.user_driver).create({
                    'waste_category_id': self.category.id,
                    'price_per_kg': 50.0,
                })

        if 'wm.monthly.billing.run' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.monthly.billing.run'].with_user(self.user_driver).create({
                    'period_start': '2026-01-01',
                    'period_end': '2026-01-31',
                })

        if 'wm.disposal.facility' in self.env:
            facility = self.env['wm.disposal.facility'].create({
                'name': 'Driver Barrier Facility',
                'facility_type': 'landfill',
            })
            with self.assertRaises(AccessError):
                self.env['wm.disposal.facility'].with_user(self.user_driver).browse(facility.id).write({
                    'name': 'Tampered Facility',
                })

    # =========================================================================
    # ROLE 2: DISPATCHER & LOGISTICS (group_wm_dispatcher)
    # =========================================================================

    def test_04_dispatcher_record_access_and_views(self):
        """Dispatcher can manage routes, collection orders, service zones, and view vehicles."""
        if 'wm.route' in self.env:
            views = self.env['wm.route'].with_user(self.user_dispatcher).get_views(
                views=[(False, 'list'), (False, 'form')]
            )
            self.assertIn('list', views.get('views', {}))
            self.assertIn('form', views.get('views', {}))

            route = self.env['wm.route'].with_user(self.user_dispatcher).create({
                'name': 'Dispatcher Route Alpha',
                'driver_id': self.user_driver.partner_id.id,
                'date': fields.Date.today(),
            })
            self.assertTrue(route.id)

        if 'wm.collection.order' in self.env:
            order = self.env['wm.collection.order'].with_user(self.user_dispatcher).create({
                'partner_id': self.partner.id,
                'collection_point_id': self.point.id if hasattr(self, 'point') else False,
                'driver_id': self.user_driver.partner_id.id,
            })
            self.assertTrue(order.id)
            order.with_context(programmatic_state_change=True).write({'state': 'dispatched'})
            self.assertEqual(order.state, 'dispatched')

    def test_05_dispatcher_security_barriers(self):
        """Dispatcher cannot create pricing rules, billing runs, or consolidated invoices."""
        if 'wm.pricing.rule' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.pricing.rule'].with_user(self.user_dispatcher).create({
                    'waste_category_id': self.category.id,
                    'price_per_kg': 15.0,
                })

        if 'wm.consolidated.invoice' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.consolidated.invoice'].with_user(self.user_dispatcher).create({
                    'partner_id': self.partner.id,
                })

    # =========================================================================
    # ROLE 3: INVENTORY & YARD OPERATOR (group_wm_inventory_operator)
    # =========================================================================

    def test_06_yard_operator_batch_workflow_and_views(self):
        """Yard operator can create batches, view forms, execute receipts and inspections."""
        if 'waste.batch' in self.env:
            views = self.env['waste.batch'].with_user(self.user_inventory).get_views(
                views=[(False, 'list'), (False, 'form')]
            )
            self.assertIn('list', views.get('views', {}))
            self.assertIn('form', views.get('views', {}))

            batch = self.env['waste.batch'].with_user(self.user_inventory).create({
                'name': 'Yard Operator Batch 101',
                'warehouse_id': self.warehouse.id,
                'location_id': self.location.id,
                'category_id': self.category.id,
                'gross_weight': 100.0,
                'tare_weight': 0.0,
                'line_ids': [(0, 0, {
                    'product_id': self.product.id,
                    'quantity': 100.0,
                    'uom_id': self.product.uom_id.id,
                })],
            })
            self.assertTrue(batch.id)

            # Yard operator can receive batch with skip inspection check context
            batch.with_context(skip_inspection_check=True).action_receive_batch()
            self.assertEqual(batch.status, 'arrived')

            # Yard operator can open collection orders in form view
            if 'wm.collection.order' in self.env:
                order = self.env['wm.collection.order'].create({'partner_id': self.partner.id})
                yard_order = self.env['wm.collection.order'].with_user(self.user_inventory).browse(order.id)
                self.assertEqual(yard_order.name, order.name)

            # Yard operator CANNOT unlink waste batches
            draft_batch = self.env['waste.batch'].create({
                'name': 'Draft Batch For Delete Test',
                'warehouse_id': self.warehouse.id,
                'location_id': self.location.id,
                'category_id': self.category.id,
            })
            with self.assertRaises(AccessError):
                self.env['waste.batch'].with_user(self.user_inventory).browse(draft_batch.id).unlink()

    def test_07_yard_operator_wizards_and_signatures(self):
        """Yard operator can execute sort wizards and digital signature requests."""
        if 'wm.signature.template' in self.env and 'wm.signature.request' in self.env:
            template = self.env['wm.signature.template'].sudo().create({
                'name': 'Yard Batch Signature Template',
            })
            sig_req = self.env['wm.signature.request'].with_user(self.user_inventory).create({
                'name': 'Yard Batch Request',
                'template_id': template.id,
            })
            self.assertTrue(sig_req.id)

    # =========================================================================
    # ROLE 4: RECYCLING SPECIALIST (group_wm_recycler)
    # =========================================================================

    def test_08_recycler_workflow_and_views(self):
        """Recycler can manage recycling orders, view forms, and advance state lifecycle."""
        if 'recycling.order' in self.env and 'waste.batch' in self.env:
            views = self.env['recycling.order'].with_user(self.user_recycler).get_views(
                views=[(False, 'list'), (False, 'form')]
            )
            self.assertIn('list', views.get('views', {}))
            self.assertIn('form', views.get('views', {}))

            batch = self.env['waste.batch'].create({
                'name': 'Recycler Source Batch',
                'warehouse_id': self.warehouse.id,
                'location_id': self.location.id,
                'category_id': self.category.id,
                'gross_weight': 200.0,
                'tare_weight': 0.0,
                'line_ids': [(0, 0, {
                    'product_id': self.product.id,
                    'quantity': 200.0,
                    'uom_id': self.product.uom_id.id,
                })],
            })
            batch.with_context(skip_inspection_check=True).action_receive_batch()

            rec_order = self.env['recycling.order'].with_user(self.user_recycler).create({
                'waste_batch_id': batch.id,
                'date_start': fields.Date.today(),
                'line_ids': [(0, 0, {
                    'product_id': self.product.id,
                    'uom_id': self.product.uom_id.id,
                    'expected_qty': 100.0,
                    'dest_location_id': self.location.id,
                })],
            })
            self.assertTrue(rec_order.id)

            rec_order.action_confirm()
            self.assertEqual(rec_order.state, 'confirmed')
            rec_order.action_start()
            self.assertEqual(rec_order.state, 'in_progress')

            # Recycler cannot unlink recycling order
            with self.assertRaises(AccessError):
                rec_order.unlink()

    def test_09_recycler_security_barriers(self):
        """Recycler cannot modify pricing rules, monthly billing runs, or routes."""
        if 'wm.pricing.rule' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.pricing.rule'].with_user(self.user_recycler).create({
                    'waste_category_id': self.category.id,
                    'price_per_kg': 20.0,
                })

        if 'wm.route' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.route'].with_user(self.user_recycler).create({
                    'name': 'Recycler Illegal Route',
                })

    # =========================================================================
    # ROLE 5: BILLING & FINANCE (group_wm_finance)
    # =========================================================================

    def test_10_finance_record_access_views_and_buttons(self):
        """Finance user can manage pricing rules, consolidated invoices, and run billing."""
        if 'wm.pricing.rule' in self.env:
            views = self.env['wm.pricing.rule'].with_user(self.user_finance).get_views(
                views=[(False, 'list'), (False, 'form')]
            )
            self.assertIn('list', views.get('views', {}))
            self.assertIn('form', views.get('views', {}))

            rule = self.env['wm.pricing.rule'].with_user(self.user_finance).create({
                'waste_category_id': self.category.id,
                'price_per_kg': 42.0,
            })
            self.assertTrue(rule.id)

        if 'wm.monthly.billing.run' in self.env:
            self.partner.write({'billing_mode': 'monthly_run'})
            if 'wm.collection.order' in self.env:
                self.env['wm.collection.order'].create({
                    'partner_id': self.partner.id,
                    'scheduled_start': '2026-02-10 10:00:00',
                    'scheduled_end': '2026-02-10 11:00:00',
                    'actual_end': '2026-02-10 11:30:00',
                    'state': 'completed',
                    'order_line_ids': [(0, 0, {
                        'category_id': self.category.id,
                        'product_id': self.product.id,
                        'weight': 100.0,
                    })],
                })
            billing_run = self.env['wm.monthly.billing.run'].with_user(self.user_finance).create({
                'period_start': '2026-02-01',
                'period_end': '2026-02-28',
                'partner_ids': [(4, self.partner.id)],
            })
            self.assertTrue(billing_run.id)
            billing_run.action_run_billing()
            self.assertEqual(billing_run.state, 'done')

        if 'wm.consolidated.invoice' in self.env:
            inv = self.env['wm.consolidated.invoice'].with_user(self.user_finance).create({
                'partner_id': self.partner.id,
            })
            self.assertTrue(inv.id)

    def test_11_finance_security_barriers(self):
        """Finance user cannot create routes, waste batches, or vehicle checklists."""
        if 'wm.route' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.route'].with_user(self.user_finance).create({
                    'name': 'Finance Forbidden Route',
                })

        if 'waste.batch' in self.env:
            with self.assertRaises(AccessError):
                self.env['waste.batch'].with_user(self.user_finance).create({
                    'name': 'Finance Forbidden Batch',
                    'warehouse_id': self.warehouse.id,
                    'location_id': self.location.id,
                    'category_id': self.category.id,
                })

    # =========================================================================
    # ROLE 6: COMPLIANCE OFFICER (group_wm_compliance_officer)
    # =========================================================================

    def test_12_compliance_officer_workflow_views_and_audit(self):
        """Compliance officer can manage facilities, manifests, certificates, and view audit logs."""
        if 'wm.disposal.facility' in self.env:
            views = self.env['wm.disposal.facility'].with_user(self.user_compliance).get_views(
                views=[(False, 'list'), (False, 'form')]
            )
            self.assertIn('list', views.get('views', {}))
            self.assertIn('form', views.get('views', {}))

            facility = self.env['wm.disposal.facility'].with_user(self.user_compliance).create({
                'name': 'GreenTech Compliance Facility',
                'facility_type': 'recycling',
            })
            self.assertTrue(facility.id)

            if 'wm.compliance.manifest' in self.env:
                manifest = self.env['wm.compliance.manifest'].with_user(self.user_compliance).create({
                    'name': 'MNF-COMP-001',
                    'generator_id': self.partner.id,
                    'transporter_id': self.user_driver.partner_id.id,
                    'disposal_facility_id': facility.id,
                    'manifest_date': fields.Date.today(),
                })
                self.assertTrue(manifest.id)
                manifest.action_submit()
                self.assertEqual(manifest.state, 'submitted')
                manifest.action_collect()
                self.assertEqual(manifest.state, 'collected')
                manifest.action_dispose()
                self.assertEqual(manifest.state, 'disposed')

            if 'wm.compliance.certificate' in self.env:
                cert = self.env['wm.compliance.certificate'].with_user(self.user_compliance).create({
                    'name': 'Disposal Certificate #889',
                    'certificate_no': 'CERT-889',
                    'facility_id': facility.id,
                    'certificate_type': 'recycling',
                    'quantity': 150.0,
                    'issued_date': fields.Date.today(),
                })
                self.assertTrue(cert.id)
                cert.action_issue()
                self.assertEqual(cert.state, 'issued')

            if 'wm.compliance.document' in self.env:
                doc = self.env['wm.compliance.document'].with_user(self.user_compliance).create({
                    'name': 'Facility Environmental Permit 2026',
                    'document_type': 'permit',
                    'expiry_date': '2028-12-31',
                    'attachment_file': base64.b64encode(b'Permit PDF Content'),
                    'attachment_filename': 'permit_2026.pdf',
                })
                self.assertTrue(doc.id)

            # Audit logs are accessible
            logs = self.env['wm.audit.log'].with_user(self.user_compliance).search([])
            self.assertIsNotNone(logs)

    def test_13_compliance_officer_security_barriers(self):
        """Compliance officer cannot create pricing rules, billing runs, or routes."""
        if 'wm.pricing.rule' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.pricing.rule'].with_user(self.user_compliance).create({
                    'waste_category_id': self.category.id,
                    'price_per_kg': 35.0,
                })

        if 'wm.route' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.route'].with_user(self.user_compliance).create({
                    'name': 'Compliance Illegal Route',
                })

    # =========================================================================
    # ROLE 7: OPERATIONS MANAGER (group_wm_ops_manager)
    # =========================================================================

    def test_14_ops_manager_supervisory_capabilities(self):
        """Operations manager can supervise dispatch, inventory, recycling, and unlink records."""
        if 'wm.route' in self.env:
            route = self.env['wm.route'].with_user(self.user_ops_mgr).create({
                'name': 'Ops Manager Supervisory Route',
            })
            self.assertTrue(route.id)
            route.unlink()

        if 'waste.batch' in self.env:
            batch = self.env['waste.batch'].with_user(self.user_ops_mgr).create({
                'name': 'Ops Manager Batch',
                'warehouse_id': self.warehouse.id,
                'location_id': self.location.id,
                'category_id': self.category.id,
            })
            self.assertTrue(batch.id)
            batch.unlink()

    # =========================================================================
    # ROLE 8: ADMINISTRATOR (group_wm_admin)
    # =========================================================================

    def test_15_admin_full_system_access(self):
        """Administrator has complete CRUD access and view loading across all WM models."""
        models_to_test = [
            'wm.waste.category',
            'wm.collection.order',
            'wm.route',
            'waste.batch',
            'recycling.order',
            'wm.pricing.rule',
            'wm.monthly.billing.run',
            'wm.disposal.facility',
            'wm.compliance.manifest',
            'wm.compliance.certificate',
        ]
        for model_name in models_to_test:
            if model_name in self.env:
                views = self.env[model_name].with_user(self.user_wm_admin).get_views(
                    views=[(False, 'list'), (False, 'form')]
                )
                self.assertIn('list', views.get('views', {}), f"Admin must be able to load list view for {model_name}")
                self.assertIn('form', views.get('views', {}), f"Admin must be able to load form view for {model_name}")

    # =========================================================================
    # UNAUTHORIZED BASE USER (base.group_user only)
    # =========================================================================

    def test_16_unauthorized_user_barriers(self):
        """Base user with no Waste Management roles cannot create or modify restricted records."""
        if 'wm.route' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.route'].with_user(self.user_unauthorized).create({
                    'name': 'Unauthorized User Route',
                })

        if 'wm.pricing.rule' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.pricing.rule'].with_user(self.user_unauthorized).create({
                    'waste_category_id': self.category.id,
                    'price_per_kg': 100.0,
                })

        if 'wm.monthly.billing.run' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.monthly.billing.run'].with_user(self.user_unauthorized).create({
                    'period_start': '2026-01-01',
                    'period_end': '2026-01-31',
                })

        if 'wm.disposal.facility' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.disposal.facility'].with_user(self.user_unauthorized).create({
                    'name': 'Unauthorized Facility',
                    'facility_type': 'landfill',
                })

        if 'wm.compliance.document' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.compliance.document'].with_user(self.user_unauthorized).create({
                    'name': 'Unauthorized Doc',
                    'document_type': 'permit',
                    'expiry_date': '2027-01-01',
                    'attachment_file': base64.b64encode(b'Fake'),
                    'attachment_filename': 'fake.pdf',
                })

        if 'wm.audit.log' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.audit.log'].with_user(self.user_unauthorized).search([])

    # =========================================================================
    # SIGN TEMPLATES: MULTIPLE SIGNATURE FIELDS VERIFICATION
    # =========================================================================

    def test_17_sign_template_signature_fields(self):
        """
        Verify that multiple Signature fields in wm.signature.template share
        proper placement, coordinate saving, role mapping, and signed PDF generation,
        and confirm that obsolete 'initial' field type is removed from the selection.
        """
        if 'wm.signature.template' not in self.env or 'wm.signature.item' not in self.env:
            return

        # Verify 'initial' is removed from type selection
        type_keys = [k for k, _v in self.env['wm.signature.item']._fields['type'].selection]
        self.assertNotIn('initial', type_keys, "'initial' should no longer be a valid type in wm.signature.item")

        role1 = self.env['wm.signature.role'].create({'name': 'Primary Signatory Role'})
        role2 = self.env['wm.signature.role'].create({'name': 'Supervisor Witness Role'})
        template = self.env['wm.signature.template'].create({
            'name': 'Dual Signature Verification Template',
            'role_ids': [(6, 0, [role1.id, role2.id])],
        })

        # 1. Add Primary Signature Field
        sig1 = self.env['wm.signature.item'].create({
            'template_id': template.id,
            'role_id': role1.id,
            'type': 'signature',
            'page': 1,
            'x': 15.0,
            'y': 75.0,
            'width': 20.0,
            'height': 4.5,
        })

        # 2. Add Supervisor Signature Field
        sig2 = self.env['wm.signature.item'].create({
            'template_id': template.id,
            'role_id': role2.id,
            'type': 'signature',
            'page': 1,
            'x': 65.0,
            'y': 75.0,
            'width': 20.0,
            'height': 4.5,
        })

        # Verification: Both signature items exist on template with their respective roles
        self.assertIn(sig1, template.item_ids)
        self.assertIn(sig2, template.item_ids)
        self.assertEqual(sig1.role_id, role1)
        self.assertEqual(sig2.role_id, role2)
        self.assertEqual(sig1.type, 'signature')
        self.assertEqual(sig2.type, 'signature')

        # Signing workflow verification with both signature fields
        if 'wm.signature.request' in self.env:
            # 1x1 transparent png for test signature image
            sample_png = (
                b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk'
                b'+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
            )
            req = self.env['wm.signature.request'].create({
                'name': 'Test Dual Signing Request',
                'template_id': template.id,
            })
            signer1 = req.signer_ids.filtered(lambda s: s.role_id == role1)[:1]
            if not signer1:
                signer1 = self.env['wm.signature.request.signer'].create({
                    'request_id': req.id,
                    'partner_id': self.partner.id,
                    'role_id': role1.id,
                })
            signer2 = req.signer_ids.filtered(lambda s: s.role_id == role2)[:1]
            if not signer2:
                signer2 = self.env['wm.signature.request.signer'].create({
                    'request_id': req.id,
                    'partner_id': self.partner.id,
                    'role_id': role2.id,
                })

            # Value for primary signature
            self.env['wm.signature.request.item.value'].create({
                'request_id': req.id,
                'item_id': sig1.id,
                'signer_id': signer1.id,
                'signature_image': sample_png,
            })

            # Value for supervisor signature
            self.env['wm.signature.request.item.value'].create({
                'request_id': req.id,
                'item_id': sig2.id,
                'signer_id': signer2.id,
                'signature_image': sample_png,
            })

            if not template.document:
                pdf_binary = template._generate_default_pdf_document()
                if pdf_binary:
                    template.write({'document': pdf_binary, 'document_filename': 'test.pdf'})

            signer1.write({'state': 'signed'})
            signer2.write({'state': 'signed'})
            # Complete request: transitions state to signed and renders both signatures
            req._check_request_completion()
            self.assertEqual(req.state, 'signed')
            self.assertTrue(req.signed_document)

    # =========================================================================
    # VERIFICATION OF REQUIREMENTS 10 - 17
    # =========================================================================

    def test_18_driver_collection_orders_views(self):
        """
        Req 10: Verify that Driver users can open Collection Orders in the required views.
        Checks list, form, and kanban views, and validates record-level reading for assigned orders.
        """
        if 'wm.collection.order' not in self.env:
            return

        views = self.env['wm.collection.order'].with_user(self.user_driver).get_views(
            views=[(False, 'list'), (False, 'form'), (False, 'kanban')]
        )
        self.assertIn('list', views.get('views', {}), "Driver must be able to load list view of Collection Orders")
        self.assertIn('form', views.get('views', {}), "Driver must be able to load form view of Collection Orders")
        self.assertIn('kanban', views.get('views', {}), "Driver must be able to load kanban view of Collection Orders")

        # Driver opens assigned order in form view without any field-level access error
        assigned_order = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'driver_id': self.user_driver.partner_id.id,
        })
        order_driver_view = self.env['wm.collection.order'].with_user(self.user_driver).browse(assigned_order.id)
        read_data = order_driver_view.read(['name', 'partner_id', 'collection_point_id', 'state', 'order_line_ids'])
        self.assertTrue(read_data, "Driver must be able to read assigned Collection Order fields")
        self.assertEqual(read_data[0]['name'], assigned_order.name)

        # 1. CREATE: Driver creates a new collection order with lines
        driver_created_order = self.env['wm.collection.order'].with_user(self.user_driver).create({
            'partner_id': self.partner.id,
            'driver_id': self.user_driver.partner_id.id,
            'estimated_weight': 150.0,
            'order_line_ids': [(0, 0, {
                'category_id': self.category.id,
                'product_id': self.product.id,
                'weight': 150.0,
            })],
        })
        self.assertTrue(driver_created_order.id, "Driver must have 'create' access to Collection Orders")

        # 2. READ: Driver reads the created collection order
        read_created = driver_created_order.with_user(self.user_driver).read(['name', 'estimated_weight', 'order_line_ids'])
        self.assertEqual(read_created[0]['estimated_weight'], 150.0, "Driver must have 'read' access to Collection Orders")

        # 3. UPDATE: Driver updates estimated weight and confirmed weight
        driver_created_order.with_user(self.user_driver).write({
            'estimated_weight': 180.0,
            'confirmed_weight': 175.0,
        })
        self.assertEqual(driver_created_order.confirmed_weight, 175.0, "Driver must have 'update' (write) access to Collection Orders")

        # 4. UNLINK: Driver must NOT have delete access (CRU only)
        with self.assertRaises(AccessError, msg="Driver must not have 'delete' access to Collection Orders (cru only)"):
            driver_created_order.with_user(self.user_driver).unlink()

    def test_19_driver_no_compliance_access(self):
        """
        Verify that Driver user does NOT have compliance access.
        Ensures Driver cannot access Disposal Facilities, Manifests, Chain of Custody,
        Certificates, Compliance Dashboard, or Report Builder.
        """
        # 1. Disposal Facility access denied
        if 'wm.disposal.facility' in self.env:
            with self.assertRaises(AccessError, msg="Driver must not have access to wm.disposal.facility"):
                self.env['wm.disposal.facility'].with_user(self.user_driver).search([])

        # 2. Compliance Manifest access denied
        if 'wm.compliance.manifest' in self.env:
            with self.assertRaises(AccessError, msg="Driver must not have access to wm.compliance.manifest"):
                self.env['wm.compliance.manifest'].with_user(self.user_driver).search([])
            with self.assertRaises(AccessError, msg="Driver must not be able to create wm.compliance.manifest"):
                self.env['wm.compliance.manifest'].with_user(self.user_driver).create({
                    'name': 'MNF-ILLEGAL-DRIVER',
                })

        # 3. Chain of Custody access denied
        if 'wm.compliance.custody' in self.env:
            with self.assertRaises(AccessError, msg="Driver must not have access to wm.compliance.custody"):
                self.env['wm.compliance.custody'].with_user(self.user_driver).search([])

        # 4. Compliance Certificate access denied
        if 'wm.compliance.certificate' in self.env:
            with self.assertRaises(AccessError, msg="Driver must not have access to wm.compliance.certificate"):
                self.env['wm.compliance.certificate'].with_user(self.user_driver).search([])

        # 5. Report Builder access denied
        if 'wm.compliance.report' in self.env:
            with self.assertRaises(AccessError, msg="Driver must not be able to load wm.compliance.report"):
                self.env['wm.compliance.report'].with_user(self.user_driver).default_get(['report_type'])
            with self.assertRaises(AccessError, msg="Driver must not be able to create wm.compliance.report"):
                self.env['wm.compliance.report'].with_user(self.user_driver).create({
                    'report_type': 'manifest',
                })

        # 6. Compliance root menu not accessible to Driver
        compliance_root = self.env.ref('wm_compliance.menu_wm_compliance_root', raise_if_not_found=False)
        if compliance_root:
            if hasattr(compliance_root, 'group_ids') and compliance_root.group_ids:
                self.assertFalse(
                    any(self.user_driver in g.user_ids for g in compliance_root.group_ids),
                    "Driver must not belong to any allowed group of the Compliance root menu"
                )
            visible_menus = self.env['ir.ui.menu'].with_user(self.user_driver)._visible_menu_ids()
            self.assertNotIn(compliance_root.id, visible_menus, "Compliance root menu must not be visible to Driver")

        self.assertFalse(self.user_driver.has_group('wm_base.group_wm_compliance_officer'))
        self.assertFalse(self.user_driver.has_group('wm_base.group_wm_ops_manager'))
        self.assertFalse(self.user_driver.has_group('wm_base.group_wm_admin'))

    def test_20_yard_operator_collection_orders_form_view(self):
        """
        Req 12: Verify that Yard Operator users can open Collection Orders in form view.
        Ensures related route, partner, order lines, and status indicators load without error.
        """
        if 'wm.collection.order' not in self.env:
            return

        route = False
        if 'wm.route' in self.env:
            route = self.env['wm.route'].create({
                'name': 'Yard Operator Inspection Route',
                'date': fields.Date.today(),
            })

        order = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'route_id': route.id if route else False,
            'order_line_ids': [(0, 0, {
                'category_id': self.category.id,
                'product_id': self.product.id,
                'weight': 350.0,
            })],
        })

        # Yard operator loads form view
        views = self.env['wm.collection.order'].with_user(self.user_inventory).get_views(
            views=[(False, 'form')]
        )
        self.assertIn('form', views.get('views', {}), "Yard operator must be able to load Collection Order form view")

        # Yard operator reads order fields including route
        order_read = self.env['wm.collection.order'].with_user(self.user_inventory).browse(order.id).read([
            'name', 'partner_id', 'route_id', 'order_line_ids', 'state', 'confirmed_weight'
        ])
        self.assertTrue(order_read, "Yard operator must be able to read Collection Order in form view")
        self.assertEqual(order_read[0]['name'], order.name)
        if route:
            self.assertEqual(order_read[0]['route_id'][0], route.id)

    def test_21_yard_operator_signs_required_documents(self):
        """
        Req 13: Verify that Yard Operator users can sign the required documents.
        Covers Waste Batch Inspection action_sign_now and digital signature requests.
        """
        # Document 1: Waste Batch Inspection
        if 'waste.batch' in self.env and 'wm.batch.inspection' in self.env:
            batch = self.env['waste.batch'].create({
                'name': 'Yard Operator Sign Batch',
                'warehouse_id': self.warehouse.id,
                'location_id': self.location.id,
                'category_id': self.category.id,
                'gross_weight': 500.0,
                'tare_weight': 50.0,
            })
            inspection = self.env['wm.batch.inspection'].create({
                'batch_id': batch.id,
                'state': 'passed',
            })
            sign_action = inspection.with_user(self.user_inventory).action_sign_now()
            self.assertEqual(sign_action.get('type'), 'ir.actions.act_url', "Yard operator must be able to sign inspection report")
            self.assertTrue(inspection.signature_template_id, "Signature template must be assigned to inspection")

        # Document 2: Direct Signature Request
        if 'wm.signature.request' in self.env and 'wm.signature.template' in self.env:
            template = self.env['wm.signature.template'].sudo().create({
                'name': 'Yard Receiving Slip Template',
            })
            req = self.env['wm.signature.request'].with_user(self.user_inventory).create({
                'name': 'Yard Goods Inward Signature Request',
                'template_id': template.id,
            })
            self.assertTrue(req.id, "Yard operator must be able to create and participate in signature requests")

    def test_22_disposal_facility_access_denied_blocks_compliance_report(self):
        """
        Req 14: Verify that users without access rights to the Disposal Facility cannot access
        the related Compliance Report option.
        """
        if 'wm.disposal.facility' not in self.env or 'wm.compliance.report' not in self.env:
            return

        # Users without access to wm.disposal.facility: user_unauthorized, user_driver, user_finance, user_inventory, user_recycler
        for user in [self.user_unauthorized, self.user_driver, self.user_finance, self.user_inventory, self.user_recycler]:
            # 1. Access to wm.disposal.facility must be denied
            with self.assertRaises(AccessError, msg=f"User {user.name} must not be allowed to access wm.disposal.facility"):
                self.env['wm.disposal.facility'].with_user(user).search([])

            # 2. Access to wm.compliance.report default_get must be blocked
            with self.assertRaises(AccessError, msg=f"User {user.name} must not be allowed to access wm.compliance.report"):
                self.env['wm.compliance.report'].with_user(user).default_get(['report_type', 'facility_id'])

            # 3. Access to wm.compliance.report create must be blocked
            with self.assertRaises(AccessError, msg=f"User {user.name} must not be allowed to create wm.compliance.report"):
                self.env['wm.compliance.report'].with_user(user).create({
                    'report_type': 'manifest',
                })

    def test_23_compliance_report_hidden_and_restricted_for_unauthorized_users(self):
        """
        Req 15: Ensure the Compliance Report option is hidden or restricted for unauthorized users.
        Verifies dashboard permissions flag and menu restrictions.
        """
        # 1. On Dashboard: can_access_report and can_access_facility must be False for unauthorized users
        if 'wm.compliance.dashboard' in self.env:
            for unauth_user in [self.user_unauthorized, self.user_driver, self.user_finance]:
                data = self.env['wm.compliance.dashboard'].with_user(unauth_user).get_dashboard_data('today')
                self.assertFalse(data.get('can_access_facility'), f"can_access_facility must be False for {unauth_user.name}")
                self.assertFalse(data.get('can_access_report'), f"can_access_report must be False for {unauth_user.name}")

            # But True for Compliance Officer and Admin
            data_officer = self.env['wm.compliance.dashboard'].with_user(self.user_compliance).get_dashboard_data('today')
            self.assertTrue(data_officer.get('can_access_facility'), "can_access_facility must be True for compliance officer")
            self.assertTrue(data_officer.get('can_access_report'), "can_access_report must be True for compliance officer")

    def test_24_billing_access_generates_invoices_successfully(self):
        """
        Req 16: Verify that users with the required Billing access rights can generate invoices successfully.
        Tests wm.consolidated.invoice.action_generate_invoice and monthly billing run.
        """
        if 'wm.consolidated.invoice' not in self.env:
            return

        order = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'scheduled_start': '2026-03-01 09:00:00',
            'scheduled_end': '2026-03-01 10:00:00',
            'actual_end': '2026-03-01 10:15:00',
            'state': 'completed',
            'order_line_ids': [(0, 0, {
                'category_id': self.category.id,
                'product_id': self.product.id,
                'weight': 250.0,
                'price': 15.0,
                'total_amount': 3750.0,
            })],
        })

        consolidated = self.env['wm.consolidated.invoice'].with_user(self.user_finance).create({
            'partner_id': self.partner.id,
            'date_from': '2026-03-01',
            'date_to': '2026-03-31',
            'order_ids': [(4, order.id)],
        })
        self.assertTrue(consolidated.id)

        # Finance user generates customer invoice
        action = consolidated.with_user(self.user_finance).action_generate_invoice()
        self.assertEqual(action.get('res_model'), 'account.move', "action_generate_invoice must return account.move action")
        self.assertEqual(consolidated.state, 'invoiced', "Consolidated invoice must be in 'invoiced' state")
        self.assertTrue(consolidated.invoice_id, "Generated account.move invoice must be linked")
        self.assertEqual(consolidated.invoice_id.move_type, 'out_invoice', "Generated invoice must be a customer invoice")
        self.assertTrue(len(consolidated.invoice_id.invoice_line_ids) > 0, "Generated invoice must contain invoice lines")

    def test_25_role_segregation_and_permitted_records_only(self):
        """
        Req 17: Ensure each user can access only the features and records permitted for their role.
        Validates boundaries between Driver, Dispatcher, Yard Operator, Recycler, Finance, and Compliance Officer.
        """
        # Driver cannot access pricing rules or billing
        if 'wm.pricing.rule' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.pricing.rule'].with_user(self.user_driver).search([])
            with self.assertRaises(AccessError):
                self.env['wm.pricing.rule'].with_user(self.user_dispatcher).create({
                    'waste_category_id': self.category.id,
                    'price_per_kg': 99.0,
                })

        # Yard Operator cannot create routes or billing runs
        if 'wm.route' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.route'].with_user(self.user_inventory).create({'name': 'Illegal Yard Route'})

        # Finance cannot create routes or batch inspections
        if 'wm.route' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.route'].with_user(self.user_finance).create({'name': 'Illegal Finance Route'})
        if 'wm.batch.inspection' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.batch.inspection'].with_user(self.user_finance).create({'state': 'passed'})

        # Unauthorized base user cannot create any WM record
        if 'wm.collection.order' in self.env:
            with self.assertRaises(AccessError):
                self.env['wm.collection.order'].with_user(self.user_unauthorized).create({'partner_id': self.partner.id})

    def test_26_compliance_officer_and_finance_open_collection_orders(self):
        """
        Verify that Compliance Officer and Billing & Finance users can open and read
        Collection Orders in form and list views without AccessError on wm.signature.request.
        """
        if 'wm.collection.order' not in self.env:
            return

        order = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
        })

        for user in [self.user_compliance, self.user_finance]:
            # Loading form and list views must succeed without signature access errors
            views = self.env['wm.collection.order'].with_user(user).get_views(
                views=[(False, 'list'), (False, 'form')]
            )
            self.assertIn('form', views.get('views', {}), f"{user.name} must be able to load form view")
            self.assertIn('list', views.get('views', {}), f"{user.name} must be able to load list view")

            # Reading signature and metadata fields must succeed cleanly
            fields_to_read = [
                'name', 'partner_id', 'state',
                'signature_signer_count', 'next_signer_id', 'next_signer_role_name'
            ]
            if 'contract_id' in order._fields:
                fields_to_read.extend(['contract_id', 'contract_product_ids'])
            if 'vehicle_id' in order._fields:
                fields_to_read.extend(['vehicle_id', 'valid_vehicle_ids'])
            read_res = order.with_user(user).read(fields_to_read)
            self.assertTrue(read_res, f"{user.name} must be able to read collection order signature fields")
            self.assertEqual(read_res[0]['name'], order.name)

    def test_27_wm_dashboard_access_option_2(self):
        """
        Verify Option 2 dashboard access:
        Authorized roles (Dispatcher, Finance, Compliance Officer, Operations Manager, Administrator)
        can view the WM Dashboard menu and retrieve dashboard metrics.
        Excluded roles (Driver, Inventory/Yard Operator, Recycler, Unauthorized)
        cannot view the menu and receive AccessError on get_dashboard_data.
        """
        dashboard_menu = self.env.ref('wm_base.menu_wm_dashboard')

        # Excluded roles cannot see the dashboard menu
        excluded_users = [
            self.user_driver,
            self.user_inventory,
            self.user_recycler,
            self.user_unauthorized,
        ]
        for user in excluded_users:
            menus = self.env['ir.ui.menu'].with_user(user)._visible_menu_ids()
            self.assertNotIn(
                dashboard_menu.id,
                menus,
                f"WM Dashboard menu must not be visible to {user.name}",
            )
            with self.assertRaises(AccessError):
                self.env['wm.dashboard'].with_user(user).get_dashboard_data('today')

        # Authorized roles can view the menu and retrieve dashboard data
        authorized_users = [
            self.user_dispatcher,
            self.user_finance,
            self.user_compliance,
            self.user_ops_mgr,
            self.user_wm_admin,
        ]
        for user in authorized_users:
            menus = self.env['ir.ui.menu'].with_user(user)._visible_menu_ids()
            self.assertIn(
                dashboard_menu.id,
                menus,
                f"WM Dashboard menu must be visible to {user.name}",
            )
            data = self.env['wm.dashboard'].with_user(user).get_dashboard_data('today')
            self.assertIsInstance(data, dict, f"Dashboard data must be returned as dict for {user.name}")
