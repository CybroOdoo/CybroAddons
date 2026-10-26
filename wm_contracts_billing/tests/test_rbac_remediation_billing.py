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
from odoo.tests import TransactionCase, tagged

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_security')
class TestRbacRemediationBilling(TransactionCase):
    """Role-based security tests for contract/billing models (moved from wm_collection)."""

    _user_count = 0

    def _create_user_with_group(self, group_xml_id):
        """
        Helper: creates a test res.users with only the specified group
        (plus base.group_user, implied).
        """
        TestRbacRemediationBilling._user_count += 1
        cnt = TestRbacRemediationBilling._user_count
        group_rec = self.env.ref(group_xml_id)
        user = self.env['res.users'].create({
            'name': f'Test Billing User {group_xml_id} {cnt}',
            'login': f'test_billing_{group_xml_id.replace(".", "_")}_{cnt}@example.com',
            'email': f'test_billing_{group_xml_id.replace(".", "_")}_{cnt}@example.com',
        })
        group_rec.write({'user_ids': [(4, user.id)]})
        return user

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
