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
###############################################################################
"""Test suite for Contacts Mass Update module."""
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestContactsMassUpdate(TransactionCase):
    """Unit tests for contacts mass update wizard and actions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_us = cls.env.ref('base.us')
        cls.state_ca = cls.env['res.country.state'].search([
            ('country_id', '=', cls.country_us.id),
            ('code', '=', 'CA')
        ], limit=1)
        cls.state_ny = cls.env['res.country.state'].search([
            ('country_id', '=', cls.country_us.id),
            ('code', '=', 'NY')
        ], limit=1)

        cls.partner_customer = cls.env['res.partner'].create({
            'name': 'Mass Update Test Customer',
            'customer_rank': 1,
            'supplier_rank': 0,
            'country_id': cls.country_us.id,
            'state_id': cls.state_ca.id,
        })
        cls.partner_vendor = cls.env['res.partner'].create({
            'name': 'Mass Update Test Vendor',
            'customer_rank': 0,
            'supplier_rank': 1,
            'country_id': cls.country_us.id,
            'state_id': cls.state_ny.id,
        })
        cls.partner_both = cls.env['res.partner'].create({
            'name': 'Mass Update Test Both',
            'customer_rank': 1,
            'supplier_rank': 1,
            'country_id': cls.country_us.id,
            'state_id': cls.state_ca.id,
        })
        cls.partner_inactive = cls.env['res.partner'].create({
            'name': 'Mass Update Inactive Partner',
            'customer_rank': 1,
            'active': False,
        })

        cls.test_user = cls.env['res.users'].create({
            'name': 'Test Salesperson',
            'login': 'test_salesperson_mass_update@test.com',
            'email': 'test_salesperson_mass_update@test.com',
        })
        cls.tag_1 = cls.env['res.partner.category'].create({'name': 'Tag 1'})
        cls.tag_2 = cls.env['res.partner.category'].create({'name': 'Tag 2'})
        cls.tag_initial = cls.env['res.partner.category'].create({'name': 'Initial Tag'})

        cls.test_company = cls.env['res.company'].create({
            'name': 'Test Subsidiary Company',
        })

        cls.payment_term = cls.env['account.payment.term'].search([], limit=1)
        cls.pricelist = cls.env['product.pricelist'].search([], limit=1)
        cls.fiscal_pos = cls.env['account.fiscal.position'].search([], limit=1)

    def test_default_get_partner_type_detection(self):
        """Test automatic detection of partner type in default_get."""
        wizard_customer = self.env['contacts.mass.update'].with_context(
            active_ids=[self.partner_customer.id]
        ).create({})
        self.assertEqual(wizard_customer.partner_type, 'customer')

        wizard_vendor = self.env['contacts.mass.update'].with_context(
            active_ids=[self.partner_vendor.id]
        ).create({})
        self.assertEqual(wizard_vendor.partner_type, 'supplier')

        wizard_both = self.env['contacts.mass.update'].with_context(
            active_ids=[self.partner_both.id]
        ).create({})
        self.assertEqual(wizard_both.partner_type, 'both')

    def test_wizard_access_rule(self):
        """Test that the Odoo 20 access rule is loaded for the wizard."""
        access = self.env.ref('contacts_mass_update.access_contacts_mass_update')
        self.assertEqual(access.model_id.model, 'contacts.mass.update')
        self.assertEqual(access.group_id, self.env.ref('base.group_user'))
        self.assertEqual(access.operation, 'crud')

    def test_partner_type_filters(self):
        """Test filtering by partner type."""
        active_ids = [self.partner_customer.id, self.partner_vendor.id, self.partner_both.id]

        wiz_cust = self.env['contacts.mass.update'].with_context(active_ids=active_ids).create({
            'partner_type': 'customer',
        })
        self.assertIn(self.partner_customer, wiz_cust.preview_partner_ids)
        self.assertNotIn(self.partner_vendor, wiz_cust.preview_partner_ids)

        wiz_supp = self.env['contacts.mass.update'].with_context(active_ids=active_ids).create({
            'partner_type': 'supplier',
        })
        self.assertIn(self.partner_vendor, wiz_supp.preview_partner_ids)
        self.assertNotIn(self.partner_customer, wiz_supp.preview_partner_ids)

    def test_location_filter_and_onchange(self):
        """Test location-based filtering and clearing via onchange."""
        active_ids = [self.partner_customer.id, self.partner_vendor.id]
        wizard = self.env['contacts.mass.update'].with_context(active_ids=active_ids).create({
            'filter_by_location': True,
            'country_ids': [(6, 0, [self.country_us.id])],
            'state_ids': [(6, 0, [self.state_ca.id])],
        })
        self.assertIn(self.partner_customer, wizard.preview_partner_ids)
        self.assertNotIn(self.partner_vendor, wizard.preview_partner_ids)

        # Test onchange when location filter is disabled
        wizard.filter_by_location = False
        wizard._onchange_filter_by_location()
        self.assertFalse(wizard.country_ids)
        self.assertFalse(wizard.state_ids)

    def test_inactive_filter(self):
        """Test inclusion of inactive partners."""
        active_ids = [self.partner_customer.id, self.partner_inactive.id]
        wiz_no_inactive = self.env['contacts.mass.update'].with_context(active_ids=active_ids).create({
            'include_inactive': False,
        })
        self.assertNotIn(self.partner_inactive, wiz_no_inactive.preview_partner_ids)

        wiz_inactive = self.env['contacts.mass.update'].with_context(active_ids=active_ids).create({
            'include_inactive': True,
        })
        self.assertIn(self.partner_inactive, wiz_inactive.preview_partner_ids)

    def test_wizard_action_next_and_back(self):
        """Test navigation between wizard steps and empty validation."""
        active_ids = [self.partner_customer.id]
        wizard = self.env['contacts.mass.update'].with_context(active_ids=active_ids).create({})

        # Advance to step 2
        next_action = wizard.action_next()
        self.assertEqual(wizard.step, 'confirm')
        self.assertEqual(next_action.get('res_model'), 'contacts.mass.update')
        self.assertEqual(next_action.get('target'), 'new')

        # Back to step 1
        back_action = wizard.action_back()
        self.assertEqual(wizard.step, 'select')
        self.assertEqual(back_action.get('res_model'), 'contacts.mass.update')

        # Error when no partner matches
        empty_wiz = self.env['contacts.mass.update'].with_context(active_ids=[]).create({
            'country_ids': [(6, 0, [self.country_us.id])],
            'state_ids': [(6, 0, [self.state_ny.id])],
            'filter_by_location': True,
            'partner_type': 'customer',  # only NY vendor exists, no NY customer
        })
        with self.assertRaises(UserError):
            empty_wiz.action_next()

    def test_action_update_partner_batch_write(self):
        """Test batch write across all supported fields including company_id."""
        self.partner_customer.category_id = [(6, 0, [self.tag_initial.id])]
        active_ids = [self.partner_customer.id, self.partner_both.id]

        wizard = self.env['contacts.mass.update'].with_context(active_ids=active_ids).create({
            'step': 'confirm',
            'tag_ids': [(6, 0, [self.tag_1.id, self.tag_2.id])],
            'replace_tags': False,
            'user_id': self.test_user.id,
            'company_id': self.test_company.id,
            'property_payment_term_id': self.payment_term.id if self.payment_term else False,
            'property_product_pricelist': self.pricelist.id if self.pricelist else False,
            'property_account_position_id': self.fiscal_pos.id if self.fiscal_pos else False,
        })

        res = wizard.action_update_partner()
        self.assertEqual(res.get('type'), 'ir.actions.client')
        self.assertEqual(res.get('tag'), 'display_notification')
        self.assertEqual(res.get('params', {}).get('type'), 'success')

        # Verify batch updates on partner_customer
        self.assertEqual(self.partner_customer.user_id, self.test_user)
        self.assertEqual(self.partner_customer.company_id, self.test_company)
        self.assertIn(self.tag_initial, self.partner_customer.category_id)
        self.assertIn(self.tag_1, self.partner_customer.category_id)
        self.assertIn(self.tag_2, self.partner_customer.category_id)

        # Test replace_tags=True
        wizard_replace = self.env['contacts.mass.update'].with_context(active_ids=[self.partner_customer.id]).create({
            'step': 'confirm',
            'tag_ids': [(6, 0, [self.tag_1.id])],
            'replace_tags': True,
        })
        wizard_replace.action_update_partner()
        self.assertEqual(self.partner_customer.category_id.ids, [self.tag_1.id])

    def test_action_update_partner_accounting_fields(self):
        """Test batch write of pricelist, payment terms, payment methods and fiscal position."""
        pricelist = self.env['product.pricelist'].create({'name': 'Mass Update Pricelist'})
        supplier_term = self.env['account.payment.term'].create({
            'name': 'Mass Update Supplier Term',
        })
        fiscal_position = self.env['account.fiscal.position'].create({
            'name': 'Mass Update Fiscal Position',
        })
        journal = self.env['account.journal'].create({
            'name': 'Mass Update Bank',
            'type': 'bank',
            'code': 'MUBNK',
        })
        inbound_line = journal.inbound_payment_method_line_ids[:1]
        outbound_line = journal.outbound_payment_method_line_ids[:1]
        self.assertTrue(inbound_line and outbound_line)

        partners = self.partner_customer | self.partner_both
        wizard = self.env['contacts.mass.update'].with_context(active_ids=partners.ids).create({
            'step': 'confirm',
            'property_product_pricelist': pricelist.id,
            'property_supplier_payment_term_id': supplier_term.id,
            'property_inbound_payment_method_line_id': inbound_line.id,
            'property_outbound_payment_method_line_id': outbound_line.id,
            'property_account_position_id': fiscal_position.id,
        })
        wizard.action_update_partner()

        for partner in partners:
            self.assertEqual(partner.property_product_pricelist, pricelist)
            self.assertEqual(partner.property_supplier_payment_term_id, supplier_term)
            self.assertEqual(partner.property_inbound_payment_method_line_id, inbound_line)
            self.assertEqual(partner.property_outbound_payment_method_line_id, outbound_line)
            self.assertEqual(partner.property_account_position_id, fiscal_position)

    def test_action_update_partner_no_partners_error(self):
        """Test UserError when action_update_partner is executed with no partners."""
        non_existent_id = max(self.env['res.partner'].search([], order='id desc', limit=1).ids or [0]) + 99999
        wizard = self.env['contacts.mass.update'].with_context(active_ids=[non_existent_id]).create({
            'step': 'confirm',
        })
        with self.assertRaises(UserError):
            wizard.action_update_partner()

    def test_server_action_execution(self):
        """Test execution of the server action on selected records."""
        server_action = self.env.ref('contacts_mass_update.action_open_contacts_mass_update')
        self.assertTrue(server_action.binding_model_id, "Server action should have binding_model_id")
        self.assertEqual(server_action.binding_model_id.model, 'res.partner')

        action_context = {
            'active_model': 'res.partner',
            'active_ids': [self.partner_customer.id, self.partner_vendor.id],
        }
        res = server_action.with_context(**action_context).run()
        self.assertEqual(res.get('type'), 'ir.actions.act_window')
        self.assertEqual(res.get('res_model'), 'contacts.mass.update')
        self.assertEqual(res.get('target'), 'new')
        self.assertEqual(res.get('view_mode'), 'form')
        self.assertEqual(res.get('context', {}).get('active_ids'), [self.partner_customer.id, self.partner_vendor.id])
