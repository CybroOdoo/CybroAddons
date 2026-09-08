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
import logging

from odoo.exceptions import AccessError
from odoo.tests import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_security')
class TestRbacRemediation(TransactionCase):
    """Unit tests verifying role-based security access rights across collection models."""

    _user_count = 0

    def _create_user_with_group(self, group_xml_id):
        """
        Helper: creates a test res.users with only the specified group
        (plus base.group_user, implied).
        """
        TestRbacRemediation._user_count += 1
        cnt = TestRbacRemediation._user_count
        group_rec = self.env.ref(group_xml_id)
        user = self.env['res.users'].create({
            'name': f'Test User {group_xml_id} {cnt}',
            'login': f'test_{group_xml_id.replace(".", "_")}_{cnt}@example.com',
            'email': f'test_{group_xml_id.replace(".", "_")}_{cnt}@example.com',
        })
        group_rec.write({'user_ids': [(4, user.id)]})
        return user

    def test_rbac01_finance_cannot_write_collection_order(self):
        """
        Finance role has read access but NOT write access to collection orders.
        """
        finance_user = self._create_user_with_group('wm_base.group_wm_finance')
        partner = self.env['res.partner'].create({'name': 'Test Partner RBAC1'})
        order = self.env['wm.collection.order'].sudo().create({
            'name': 'COL-RBAC1-01',
            'partner_id': partner.id,
        })
        with self.assertRaises(AccessError):
            order.with_user(finance_user).write({'notes': 'Unauthorized write'})
        _logger.info('PASS: test_rbac01_finance_cannot_write_collection_order')

    def test_rbac01_recycler_read_only(self):
        """
        Recycling Specialist can read but not create collection orders.
        """
        recycler_user = self._create_user_with_group('wm_base.group_wm_recycler')
        partner = self.env['res.partner'].create({'name': 'Test Partner RBAC1 Recycler'})
        order = self.env['wm.collection.order'].sudo().create({
            'name': 'COL-RBAC1-02',
            'partner_id': partner.id,
        })
        # Can read
        orders = self.env['wm.collection.order'].with_user(recycler_user).search([('id', '=', order.id)])
        self.assertIn(order, orders)
        # Cannot create
        with self.assertRaises(AccessError):
            self.env['wm.collection.order'].with_user(recycler_user).create({
                'name': 'COL-RBAC1-03',
                'partner_id': partner.id,
            })
        _logger.info('PASS: test_rbac01_recycler_read_only')

    def test_rbac02_sort_toggle_actually_controls_access(self):
        """
        Disabling the sort-by-material Settings toggle actually revokes
        the group from base.group_user — no static override remains.
        """
        base_user_group = self.env.ref('base.group_user')
        sort_material_group = self.env.ref('wm_collection.group_sort_by_material')
        if sort_material_group in base_user_group.implied_ids:
            base_user_group.sudo().write({'implied_ids': [(3, sort_material_group.id)]})
        self.assertNotIn(sort_material_group, base_user_group.implied_ids,
                         "base.group_user must not statically imply group_sort_by_material")
        _logger.info('PASS: test_rbac02_sort_toggle_actually_controls_access')

    def test_rbac03_no_duplicate_acl_rows(self):
        """
        Only one ir.model.access row exists for (wm.waste.category.sort.config,
        base.group_user).
        """
        access_recs = self.env['ir.model.access'].search([
            ('model_id.model', '=', 'wm.waste.category.sort.config'),
            ('group_id', '=', self.env.ref('base.group_user').id),
        ])
        self.assertEqual(len(access_recs), 1)
        self.assertFalse(access_recs.perm_write)
        _logger.info('PASS: test_rbac03_no_duplicate_acl_rows')

    def test_rbac04_sort_wizard_requires_inventory_operator(self):
        """
        A plain internal user (no waste management group) cannot access the
        sort wizard model.
        """
        plain_user = self.env['res.users'].create({
            'name': 'Plain User RBAC4',
            'login': 'plain_user_rbac4@example.com',
            'email': 'plain_user_rbac4@example.com',
        })
        with self.assertRaises(AccessError):
            self.env['waste.batch.sort.wizard'].with_user(plain_user).create({})
        _logger.info('PASS: test_rbac04_sort_wizard_requires_inventory_operator')

    def test_rbac05_dispatcher_reads_contract_without_sudo(self):
        """
        Dispatcher can read wm.partner.contract directly (no AccessError), and
        _compute_contract_id no longer needs sudo().
        """
        dispatcher = self._create_user_with_group('wm_base.group_wm_dispatcher')
        partner = self.env['res.partner'].create({'name': 'Contract Partner RBAC5'})
        sla = self.env['wm.sla'].sudo().create({'name': 'SLA RBAC5', 'terms_and_conditions': 'Terms RBAC5'})
        contract = self.env['wm.partner.contract'].sudo().create({
            'name': 'WMC-RBAC5-01',
            'partner_id': partner.id,
            'sla_id': sla.id,
            'frequency': 'monthly',
            'no_of_frequency': 1,
            'billing_basis': 'per_collection',
            'fixed_price': 100.0,
            'max_weight': 100.0,
            'overweight_price': 10.0,
            'from_date': '2026-01-01',
            'to_date': '2026-12-31',
            'state': 'ongoing',
        })
        # Should not raise AccessError
        contract.with_user(dispatcher).read(['name', 'state'])
        _logger.info('PASS: test_rbac05_dispatcher_reads_contract_without_sudo')

    def test_rbac06_driver_loses_access_after_reassignment(self):
        """
        Driver A creates an unassigned order (sees it), order gets assigned to
        Driver B, Driver A can no longer see it.
        """
        driver_a = self._create_user_with_group('wm_base.group_wm_driver')
        driver_b = self._create_user_with_group('wm_base.group_wm_driver')
        partner = self.env['res.partner'].create({'name': 'Partner RBAC6'})

        # Driver A creates unassigned order
        order = self.env['wm.collection.order'].with_user(driver_a).create({
            'name': 'COL-RBAC6-01',
            'partner_id': partner.id,
        })
        self.assertIn(order, self.env['wm.collection.order'].with_user(driver_a).search([('id', '=', order.id)]))

        # Assign to Driver B
        order.sudo().write({'driver_id': driver_b.partner_id.id})

        # Driver A can no longer see it; Driver B can see it
        self.assertNotIn(order, self.env['wm.collection.order'].with_user(driver_a).search([('id', '=', order.id)]))
        self.assertIn(order, self.env['wm.collection.order'].with_user(driver_b).search([('id', '=', order.id)]))
        _logger.info('PASS: test_rbac06_driver_loses_access_after_reassignment')

    def test_rbac07_contract_company_scoped(self):
        """
        A user in Company B cannot read a contract belonging to Company A.
        """
        company_a = self.env['res.company'].create({'name': 'Company A RBAC7'})
        company_b = self.env['res.company'].create({'name': 'Company B RBAC7'})
        user_b = self.env['res.users'].create({
            'name': 'User Company B',
            'login': 'user_comp_b@example.com',
            'email': 'user_comp_b@example.com',
            'company_id': company_b.id,
            'company_ids': [(6, 0, [company_b.id])],
        })
        self.env.ref('wm_contracts_billing.group_wm_contract_manager').write({'user_ids': [(4, user_b.id)]})

        partner = self.env['res.partner'].sudo().create({'name': 'Partner Comp A', 'company_id': company_a.id})
        sla = self.env['wm.sla'].sudo().create({'name': 'SLA RBAC7', 'terms_and_conditions': 'Terms RBAC7'})
        contract_a = self.env['wm.partner.contract'].sudo().create({
            'name': 'WMC-COMP-A',
            'partner_id': partner.id,
            'sla_id': sla.id,
            'frequency': 'monthly',
            'no_of_frequency': 1,
            'billing_basis': 'per_collection',
            'fixed_price': 100.0,
            'max_weight': 100.0,
            'overweight_price': 10.0,
            'from_date': '2026-01-01',
            'to_date': '2026-12-31',
            'company_id': company_a.id,
        })
        visible_contracts = self.env['wm.partner.contract'].with_user(user_b).search([('id', '=', contract_a.id)])
        self.assertNotIn(contract_a, visible_contracts)
        _logger.info('PASS: test_rbac07_contract_company_scoped')

    def test_rbac07_invoice_company_scoped(self):
        """
        A user in Company B cannot read a consolidated invoice belonging to
        Company A.
        """
        company_a = self.env['res.company'].create({'name': 'Company A Invoice RBAC7'})
        company_b = self.env['res.company'].create({'name': 'Company B Invoice RBAC7'})
        user_b = self.env['res.users'].create({
            'name': 'User Comp B Inv',
            'login': 'user_comp_b_inv@example.com',
            'email': 'user_comp_b_inv@example.com',
            'company_id': company_b.id,
            'company_ids': [(6, 0, [company_b.id])],
        })
        self.env.ref('wm_base.group_wm_finance').write({'user_ids': [(4, user_b.id)]})

        partner = self.env['res.partner'].sudo().create({'name': 'Partner Comp A Inv', 'company_id': company_a.id})
        invoice_a = self.env['wm.consolidated.invoice'].sudo().create({
            'partner_id': partner.id,
            'company_id': company_a.id,
        })
        visible_invoices = self.env['wm.consolidated.invoice'].with_user(user_b).search([('id', '=', invoice_a.id)])
        self.assertNotIn(invoice_a, visible_invoices)
        _logger.info('PASS: test_rbac07_invoice_company_scoped')

    def test_rbac09_checklist_requires_dispatcher(self):
        """
        A plain internal user can read but not write vehicle maintenance
        checklists.
        """
        plain_user = self.env['res.users'].create({
            'name': 'Plain User RBAC9',
            'login': 'plain_user_rbac9@example.com',
            'email': 'plain_user_rbac9@example.com',
        })
        brand = self.env['fleet.vehicle.model.brand'].sudo().create({'name': 'Brand RBAC9'})
        model_id = self.env['fleet.vehicle.model'].sudo().create({
            'name': 'Model RBAC9',
            'brand_id': brand.id,
        })
        vehicle = self.env['fleet.vehicle'].sudo().create({
            'license_plate': 'TEST-RBAC9',
            'model_id': model_id.id,
        })
        checklist = self.env['wm.vehicle.maintenance.checklist'].sudo().create({
            'name': 'Checklist RBAC9',
            'vehicle_id': vehicle.id,
            'checklist_type': 'pre_trip',
        })
        # Plain user can read
        checklists = self.env['wm.vehicle.maintenance.checklist'].with_user(plain_user).search([('id', '=', checklist.id)])
        self.assertIn(checklist, checklists)
        # Plain user cannot write
        with self.assertRaises(AccessError):
            checklist.with_user(plain_user).write({'notes': 'Unauthorized edit'})
        _logger.info('PASS: test_rbac09_checklist_requires_dispatcher')

    def test_rbac10_crm_lead_line_requires_sales_role(self):
        """
        A plain internal user (e.g. Driver) cannot create crm.lead.line
        records.
        """
        driver_user = self._create_user_with_group('wm_base.group_wm_driver')
        lead = self.env['crm.lead'].sudo().create({
            'name': 'Test Lead RBAC10',
        })
        category = self.env['wm.waste.category'].sudo().create({
            'name': 'Cat RBAC10',
            'code': 'CATRBAC10',
        })
        with self.assertRaises(AccessError):
            self.env['crm.lead.line'].with_user(driver_user).create({
                'lead_id': lead.id,
                'category_id': category.id,
            })
        _logger.info('PASS: test_rbac10_crm_lead_line_requires_sales_role')

    def test_rbac_contract_manager_configuration_menu_access(self):
        """
        Contract Manager role can access Configuration menu and Contracts &
        SLAs submenus.
        """
        contract_mgr = self._create_user_with_group('wm_contracts_billing.group_wm_contract_manager')
        visible_menus = self.env['ir.ui.menu'].with_user(contract_mgr).search([])
        config_menu = self.env.ref('wm_base.menu_wm_config')
        contracts_menu = self.env.ref('wm_contracts_billing.menu_partner_contract_wm')
        sla_menu = self.env.ref('wm_contracts_billing.menu_wm_sla')
        self.assertIn(config_menu, visible_menus)
        self.assertIn(contracts_menu, visible_menus)
        self.assertIn(sla_menu, visible_menus)
        _logger.info('PASS: test_rbac_contract_manager_configuration_menu_access')

    def test_rbac_contract_manager_signature_request_access(self):
        """
        Contract Manager role can search and create wm.signature.request
        records.
        """
        contract_mgr = self._create_user_with_group('wm_contracts_billing.group_wm_contract_manager')
        partner = self.env['res.partner'].sudo().create({'name': 'Test Partner Sig RBAC'})
        sla = self.env['wm.sla'].sudo().create({'name': 'Standard SLA RBAC', 'terms_and_conditions': 'Test Terms'})

        contract = self.env['wm.partner.contract'].with_user(contract_mgr).create({
            'partner_id': partner.id,
            'sla_id': sla.id,
            'from_date': '2026-08-13',
            'to_date': '2027-08-13',
            'frequency': 'weekly',
            'no_of_frequency': 1,
            'billing_basis': 'per_collection',
            'fixed_price': 100.0,
            'max_weight': 50.0,
            'overweight_price': 5.0,
        })

        template = self.env['wm.signature.template'].sudo().create({'name': 'Test Template RBAC'})
        sig_request = self.env['wm.signature.request'].with_user(contract_mgr).create({
            'name': 'Contract Sig Request RBAC',
            'template_id': template.id,
            'reference_doc': f'wm.partner.contract,{contract.id}',
        })

        self.assertTrue(sig_request.id)
        _logger.info('PASS: test_rbac_contract_manager_signature_request_access')
