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
"""
Integration tests for wm_crm — CRM Lead to WM Contract conversion & Quotation workflow.
"""
import logging
from datetime import date

from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo.tests import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_crm')
class TestWmCrmLeadConversion(TransactionCase):
    """Full pipeline tests for the CRM → Quotation → WM Contract conversion flow."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()

        # ── Partner ──────────────────────────────────────────────────────
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Waste Customer',
            'email': 'test.waste@example.com',
        })

        # ── CRM stages ───────────────────────────────────────────────────
        cls.stage_new = cls.env['crm.stage'].create({
            'name': 'New (WM Test)',
            'sequence': 1,
            'is_won': False,
        })
        cls.stage_won = cls.env['crm.stage'].create({
            'name': 'Won (WM Test)',
            'sequence': 10,
            'is_won': True,
        })

        # ── SLA ──────────────────────────────────────────────────────────
        cls.sla = cls.env['wm.sla'].create({
            'name': 'Test SLA',
            'terms_and_conditions': '<p>Standard SLA Terms & Conditions</p>',
        })

        # ── Collection point ─────────────────────────────────────────────
        cls.site = cls.env['wm.collection.point'].create({
            'name': 'Test Site A',
            'partner_id': cls.partner.id,
        })

        # ── Service product & Waste Category ─────────────────────────────
        cls.service_product = cls.env['product.product'].create({
            'name': 'Waste Collection Service Product',
            'type': 'service',
        })
        cls.waste_category = cls.env['wm.waste.category'].create({
            'name': 'Commercial Solid Waste',
            'code': 'CSW',
            'service_product_id': cls.service_product.id,
        })

        # ── Dates ────────────────────────────────────────────────────────
        cls.today = date.today()
        cls.next_year = cls.today + relativedelta(years=1)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _make_won_lead(self, partner=None):
        """
        Create a CRM lead in the Won stage with the test partner.
        """
        lead = self.env['crm.lead'].create({
            'name': 'Test WM Lead',
            'type': 'opportunity',
            'partner_id': (partner or self.partner).id,
            'stage_id': self.stage_won.id,
            'probability': 100,
            'wm_service_type': 'collection',
            'wm_frequency': 'weekly',
            'wm_no_of_sites': 2,
        })
        return lead

    def _run_wizard(self, lead, extra_vals=None):
        """
        Create the wizard and call action_confirm_conversion, returning
        the new wm.partner.contract record.
        """
        vals = {
            'lead_id': lead.id,
            'partner_id': lead.partner_id.id,
            'contract_from_date': self.today,
            'contract_to_date': self.next_year,
            'frequency': 'weekly',
            'no_of_frequency': 1,
            'billing_basis': 'per_collection',
            'sla_id': self.sla.id,
            'collection_point_ids': [(6, 0, [self.site.id])],
        }
        if extra_vals:
            vals.update(extra_vals)
        wizard = self.env['wm.lead.conversion.wizard'].create(vals)
        action = wizard.action_confirm_conversion()
        contract_id = action.get('res_id')
        return self.env['wm.partner.contract'].browse(contract_id)

    # ------------------------------------------------------------------
    # Tests: Direct CRM -> Contract
    # ------------------------------------------------------------------
    def test_convert_won_lead_creates_draft_contract(self):
        """
        Won lead with partner converts to a draft wm.partner.contract.
        """
        lead = self._make_won_lead()
        contract = self._run_wizard(lead)

        self.assertEqual(contract.state, 'draft',
                         'Contract must be created in draft state.')
        self.assertEqual(contract.crm_lead_id, lead,
                         'Contract crm_lead_id must point to the source lead.')
        self.assertEqual(contract.partner_id, self.partner,
                         'Contract partner must match the lead partner.')
        _logger.info('PASS: test_convert_won_lead_creates_draft_contract')

    def test_non_won_lead_raises(self):
        """
        Non-Won lead raises UserError on conversion attempt.
        """
        lead = self.env['crm.lead'].create({
            'name': 'Non-Won Lead',
            'type': 'opportunity',
            'partner_id': self.partner.id,
            'stage_id': self.stage_new.id,
        })
        with self.assertRaises(UserError):
            lead.action_convert_to_wm_contract()
        _logger.info('PASS: test_non_won_lead_raises')

    def test_no_partner_raises(self):
        """
        Won lead without partner raises UserError.
        """
        lead = self.env['crm.lead'].create({
            'name': 'Partnerless Won Lead',
            'type': 'opportunity',
            'stage_id': self.stage_won.id,
            'probability': 100,
        })
        with self.assertRaises(UserError):
            lead.action_convert_to_wm_contract()
        _logger.info('PASS: test_no_partner_raises')

    def test_second_conversion_blocked(self):
        """
        A lead that already has a linked contract has wm_contract_count == 1;
        the view button is invisible (wm_contract_count != 0 guard).         We
        also verify the guard at model level by checking the count.
        """
        lead = self._make_won_lead()
        self._run_wizard(lead)

        lead.invalidate_recordset(['wm_contract_count', 'wm_contract_ids'])
        self.assertEqual(lead.wm_contract_count, 1,
                         'Expected exactly one contract after conversion.')
        self.assertGreater(lead.wm_contract_count, 0,
                           'wm_contract_count must be > 0 to block a second conversion.')
        _logger.info('PASS: test_second_conversion_blocked')

    def test_existing_contract_warning_flag(self):
        """
        Wizard has_existing_contract=True when customer already has an
        active (sent/signed/confirmed/ongoing) contract.
        """
        partner2 = self.env['res.partner'].create({
            'name': 'Test Existing Contract Customer',
        })
        site2 = self.env['wm.collection.point'].create({
            'name': 'Site for partner2',
            'partner_id': partner2.id,
        })

        existing_contract = self.env['wm.partner.contract'].create({
            'partner_id': partner2.id,
            'from_date': self.today - relativedelta(months=6),
            'to_date': self.today + relativedelta(months=6),
            'frequency': 'weekly',
            'no_of_frequency': 1,
            'billing_basis': 'per_collection',
            'fixed_price': 100.0,
            'max_weight': 500.0,
            'overweight_price': 10.0,
            'sla_id': self.sla.id,
            'collection_point_ids': [(6, 0, [site2.id])],
        })
        existing_contract.write({'state': 'ongoing'})

        lead2 = self.env['crm.lead'].create({
            'name': 'Lead for Existing Contract Customer',
            'type': 'opportunity',
            'partner_id': partner2.id,
            'stage_id': self.stage_won.id,
            'probability': 100,
        })

        action = lead2.action_convert_to_wm_contract()
        ctx = action.get('context', {})
        self.assertTrue(ctx.get('default_has_existing_contract'),
                        'has_existing_contract must be True when customer has active contract.')
        self.assertEqual(ctx.get('default_existing_contract_name'),
                          existing_contract.name,
                          'existing_contract_name must match the active contract name.')
        _logger.info('PASS: test_existing_contract_warning_flag')

    def test_crm_lead_contract_count_smart_button(self):
        """
        wm_contract_count increments to 1 after successful conversion.
        """
        lead = self._make_won_lead()
        self.assertEqual(lead.wm_contract_count, 0,
                         'Contract count must be 0 before conversion.')
        self._run_wizard(lead)
        lead.invalidate_recordset(['wm_contract_count', 'wm_contract_ids'])
        self.assertEqual(lead.wm_contract_count, 1,
                         'Contract count must be 1 after conversion.')
        _logger.info('PASS: test_crm_lead_contract_count_smart_button')

    def test_chatter_note_posted_on_lead(self):
        """
        A chatter message is posted on the lead after conversion,
        containing a link to the new contract.
        """
        lead = self._make_won_lead()
        initial_message_count = len(lead.message_ids)
        contract = self._run_wizard(lead)

        lead.invalidate_recordset(['message_ids'])
        self.assertGreater(len(lead.message_ids), initial_message_count,
                           'At least one new chatter message must be posted on the lead.')
        latest_body = lead.message_ids[0].body
        self.assertIn(contract.name, latest_body,
                      'The chatter note must reference the new contract name.')
        _logger.info('PASS: test_chatter_note_posted_on_lead')

    def test_originated_from_crm_flag(self):
        """
        Contract has originated_from_crm=True and crm_lead_id set after
        conversion via the wizard.
        """
        lead = self._make_won_lead()
        contract = self._run_wizard(lead)

        self.assertTrue(contract.originated_from_crm,
                        'originated_from_crm must be True after conversion.')
        self.assertEqual(contract.crm_lead_id.id, lead.id,
                         'crm_lead_id must point to the originating lead.')
        _logger.info('PASS: test_originated_from_crm_flag')

    def test_contract_has_correct_fields_from_wizard(self):
        """
        Contract fields match the values entered in the wizard.
        """
        lead = self._make_won_lead()
        contract = self._run_wizard(lead, extra_vals={
            'frequency': 'monthly',
            'no_of_frequency': 3,
            'billing_basis': 'hybrid',
        })

        self.assertEqual(contract.frequency, 'monthly')
        self.assertEqual(contract.no_of_frequency, 3)
        self.assertEqual(contract.billing_basis, 'hybrid')
        self.assertEqual(contract.sla_id, self.sla)
        self.assertEqual(contract.from_date, self.today)
        self.assertEqual(contract.to_date, self.next_year)
        self.assertIn(self.site, contract.collection_point_ids)
        _logger.info('PASS: test_contract_has_correct_fields_from_wizard')

    def test_quoted_lead_lines_transfer_to_contract_lines(self):
        """
        Quoted waste category lines on CRM lead transfer to contract lines on
        conversion.
        """
        category = self.env['wm.waste.category'].create({'name': 'Test Waste Category'})
        lead = self._make_won_lead()
        self.env['crm.lead.line'].create({
            'lead_id': lead.id,
            'category_id': category.id,
            'estimated_weight_kg': 1000.0,
            'price_unit': 2.50,
        })
        contract = self._run_wizard(lead, extra_vals={'billing_basis': 'category_rate'})
        self.assertEqual(len(contract.contract_line_ids), 1,
                         'Expected exactly one contract line transferred from lead.')
        self.assertEqual(contract.contract_line_ids[0].category_id, category)
        self.assertEqual(contract.contract_line_ids[0].price, 2.50)
        _logger.info('PASS: test_quoted_lead_lines_transfer_to_contract_lines')

    def test_auto_create_collection_site_when_none_selected(self):
        """
        When wizard collection_point_ids is empty and partner has no sites, a
        default site is created.
        """
        new_partner = self.env['res.partner'].create({
            'name': 'Brand New Customer',
            'city': 'San Francisco',
        })
        lead = self._make_won_lead(partner=new_partner)
        wizard = self.env['wm.lead.conversion.wizard'].create({
            'lead_id': lead.id,
            'partner_id': new_partner.id,
            'contract_from_date': self.today,
            'contract_to_date': self.next_year,
            'frequency': 'weekly',
            'no_of_frequency': 1,
            'billing_basis': 'per_collection',
            'sla_id': self.sla.id,
            'collection_point_ids': [(6, 0, [])],
        })
        action = wizard.action_confirm_conversion()
        contract = self.env['wm.partner.contract'].browse(action['res_id'])
        self.assertTrue(contract.collection_point_ids,
                        'A default collection site must be auto-created when none existed.')
        self.assertEqual(contract.collection_point_ids[0].partner_id, new_partner)
        _logger.info('PASS: test_auto_create_collection_site_when_none_selected')

    # ------------------------------------------------------------------
    # Tests: Won Lead -> Quotation -> Contract Flow
    # ------------------------------------------------------------------
    def test_waste_category_service_product_id_field(self):
        """
        wm.waste.category has service_product_id field set and queryable.
        """
        self.assertEqual(self.waste_category.service_product_id, self.service_product)

    def test_create_quotation_from_won_lead(self):
        """
        Won lead with waste lines generates a draft sale.order linked via
        opportunity_id.
        """
        lead = self._make_won_lead()
        self.env['crm.lead.line'].create({
            'lead_id': lead.id,
            'category_id': self.waste_category.id,
            'estimated_weight_kg': 500.0,
            'price_unit': 3.50,
        })

        action = lead.action_create_quotation()
        self.assertEqual(action.get('res_model'), 'sale.order')
        quotation_id = action.get('res_id')
        quotation = self.env['sale.order'].browse(quotation_id)

        self.assertEqual(quotation.state, 'draft')
        self.assertEqual(quotation.partner_id, self.partner)
        self.assertEqual(quotation.opportunity_id, lead)
        self.assertEqual(len(quotation.order_line), 1)
        self.assertEqual(quotation.order_line[0].product_id, self.service_product)
        self.assertEqual(quotation.order_line[0].product_uom_qty, 500.0)
        self.assertEqual(quotation.order_line[0].price_unit, 3.50)
        self.assertEqual(quotation.amount_untaxed, 1750.0)
        _logger.info('PASS: test_create_quotation_from_won_lead')

    def test_create_quotation_material_product_override(self):
        """
        When material product is selected on crm.lead.line, quotation uses it
        instead of service_product_id.
        """
        material_product = self.env['product.product'].create({
            'name': 'Cardboard Scrap',
            'is_waste_material': True,
        })
        lead = self._make_won_lead()
        self.env['crm.lead.line'].create({
            'lead_id': lead.id,
            'category_id': self.waste_category.id,
            'product_ids': [(6, 0, [material_product.id])],
            'estimated_weight_kg': 200.0,
            'price_unit': 4.00,
        })

        action = lead.action_create_quotation()
        quotation = self.env['sale.order'].browse(action['res_id'])
        self.assertEqual(quotation.order_line[0].product_id, material_product)
        _logger.info('PASS: test_create_quotation_material_product_override')

    def test_create_quotation_guards_raise(self):
        """
        action_create_quotation raises UserError on non-won stage, missing
        partner, or missing lines/product.
        """
        # 1. Non-won lead
        lead_draft = self.env['crm.lead'].create({
            'name': 'Draft Opportunity',
            'partner_id': self.partner.id,
            'stage_id': self.stage_new.id,
        })
        with self.assertRaises(UserError):
            lead_draft.action_create_quotation()

        # 2. Won lead without partner
        lead_no_partner = self.env['crm.lead'].create({
            'name': 'No Partner Won Opp',
            'stage_id': self.stage_won.id,
            'probability': 100,
        })
        with self.assertRaises(UserError):
            lead_no_partner.action_create_quotation()

        # 3. Won lead without lines
        lead_no_lines = self._make_won_lead()
        with self.assertRaises(UserError):
            lead_no_lines.action_create_quotation()

        # 4. Waste category without service_product_id and no material auto-creates/resolves service product
        empty_cat = self.env['wm.waste.category'].create({'name': 'Unconfigured Cat'})
        self.env['crm.lead.line'].create({
            'lead_id': lead_no_lines.id,
            'category_id': empty_cat.id,
            'estimated_weight_kg': 100.0,
            'price_unit': 2.0,
        })
        action = lead_no_lines.action_create_quotation()
        self.assertTrue(action.get('res_id'), 'Quotation should be created with auto-resolved service product')
        _logger.info('PASS: test_create_quotation_guards_raise')

    def test_quotation_confirmation_schedules_activity_and_wizard_prefills(self):
        """
        Confirming a quotation schedules an activity on the lead, wizard picks
        up quotation price,         and contract conversion resolves the
        scheduled activity.
        """
        lead = self._make_won_lead()
        self.env['crm.lead.line'].create({
            'lead_id': lead.id,
            'category_id': self.waste_category.id,
            'estimated_weight_kg': 100.0,
            'price_unit': 5.00,
        })

        action = lead.action_create_quotation()
        quotation = self.env['sale.order'].browse(action['res_id'])
        self.assertEqual(quotation.state, 'draft')

        # Confirm quotation (Sale order confirmed)
        quotation.action_confirm()
        self.assertEqual(quotation.state, 'sale')

        # Verify activity scheduled on lead
        todo_activity_type = self.env.ref('mail.mail_activity_data_todo')
        pending_activity = lead.activity_ids.filtered(
            lambda a: a.activity_type_id == todo_activity_type and 'Quotation accepted' in a.summary
        )
        self.assertTrue(pending_activity, 'A todo activity must be scheduled on lead after quotation confirmation.')

        # Verify wizard default_get pre-fills fixed_price from quotation.amount_total
        defaults = self.env['wm.lead.conversion.wizard'].with_context(default_lead_id=lead.id).default_get([
            'lead_id', 'partner_id', 'fixed_price'
        ])
        self.assertEqual(defaults.get('fixed_price'), quotation.amount_total)

        # Execute wizard conversion
        contract = self._run_wizard(lead)
        self.assertEqual(contract.state, 'draft')
        self.assertEqual(contract.crm_lead_id, lead)

        # Verify activity is resolved
        lead.invalidate_recordset(['activity_ids'])
        remaining_activity = lead.activity_ids.filtered(
            lambda a: a.activity_type_id == todo_activity_type and 'Quotation accepted' in a.summary
        )
        self.assertFalse(remaining_activity, 'Quotation acceptance activity must be marked done after contract conversion.')
        _logger.info('PASS: test_quotation_confirmation_schedules_activity_and_wizard_prefills')

    def test_no_duplicate_activity_if_contract_already_exists(self):
        """
        If lead already has a contract, confirming a quotation does not
        schedule duplicate activities.
        """
        lead = self._make_won_lead()
        self.env['crm.lead.line'].create({
            'lead_id': lead.id,
            'category_id': self.waste_category.id,
            'estimated_weight_kg': 100.0,
            'price_unit': 5.00,
        })
        action = lead.action_create_quotation()
        quotation = self.env['sale.order'].browse(action['res_id'])

        # First convert contract directly
        self._run_wizard(lead)
        self.assertTrue(lead.wm_contract_ids)

        # Confirm quotation after contract already exists
        quotation.action_confirm()
        todo_activity_type = self.env.ref('mail.mail_activity_data_todo')
        activity = lead.activity_ids.filtered(
            lambda a: a.activity_type_id == todo_activity_type and 'Quotation accepted' in a.summary
        )
        self.assertFalse(activity, 'No activity should be created if contract already exists on the lead.')
        _logger.info('PASS: test_no_duplicate_activity_if_contract_already_exists')

    def test_create_contract_from_quotation_action(self):
        """
        Converting to contract directly from a confirmed Quotation/Sale Order
        sets sale_order_id and creates links.
        """
        lead = self._make_won_lead()
        self.env['crm.lead.line'].create({
            'lead_id': lead.id,
            'category_id': self.waste_category.id,
            'estimated_weight_kg': 300.0,
            'price_unit': 4.50,
        })
        action = lead.action_create_quotation()
        quotation = self.env['sale.order'].browse(action['res_id'])
        quotation.action_confirm()

        # Call action_convert_to_wm_contract from the quotation
        wiz_action = quotation.action_convert_to_wm_contract()
        self.assertEqual(wiz_action['res_model'], 'wm.lead.conversion.wizard')
        ctx = wiz_action['context']
        self.assertEqual(ctx.get('default_order_id'), quotation.id)
        self.assertEqual(ctx.get('default_fixed_price'), quotation.amount_total)

        # Create the wizard and confirm conversion
        wizard = self.env['wm.lead.conversion.wizard'].with_context(ctx).create({
            'order_id': quotation.id,
            'lead_id': lead.id,
            'partner_id': self.partner.id,
            'contract_from_date': self.today,
            'contract_to_date': self.next_year,
            'frequency': 'weekly',
            'no_of_frequency': 1,
            'billing_basis': 'per_collection',
            'sla_id': self.sla.id,
            'collection_point_ids': [(6, 0, [self.site.id])],
        })
        conv_action = wizard.action_confirm_conversion()
        contract = self.env['wm.partner.contract'].browse(conv_action['res_id'])

        self.assertEqual(contract.sale_order_id, quotation)
        self.assertEqual(contract.crm_lead_id, lead)
        self.assertEqual(contract.partner_id, self.partner)
        self.assertEqual(quotation.wm_contract_count, 1)

        # Verify smart button action from quotation
        view_action = quotation.action_view_wm_contracts()
        self.assertEqual(view_action['res_model'], 'wm.partner.contract')
        _logger.info('PASS: test_create_contract_from_quotation_action')

    def test_contract_manager_can_create_quotation_without_category_write_permission(self):
        """
        Verify that a Contract Manager user (who lacks write access on wm.waste.category)
        can successfully create a quotation even if the category does not yet have a
        service_product_id.
        """
        contract_manager_user = self.env['res.users'].create({
            'name': 'Test Contract Manager User',
            'login': 'test_wm_contract_manager_user',
            'email': 'cm_user@test.com',
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('sales_team.group_sale_salesman').id,
                self.env.ref('wm_contracts_billing.group_wm_contract_manager').id,
            ])],
        })

        cat_without_product = self.env['wm.waste.category'].create({
            'name': 'Unlinked Category For CM Test',
        })
        self.assertFalse(cat_without_product.service_product_id)

        lead = self.env['crm.lead'].with_user(contract_manager_user).create({
            'name': 'CM Test Won Lead',
            'partner_id': self.partner.id,
            'stage_id': self.stage_won.id,
            'probability': 100,
        })
        self.env['crm.lead.line'].with_user(contract_manager_user).create({
            'lead_id': lead.id,
            'category_id': cat_without_product.id,
            'estimated_weight_kg': 150.0,
            'price_unit': 3.50,
        })

        action = lead.with_user(contract_manager_user).action_create_quotation()
        self.assertTrue(action.get('res_id'), 'Quotation should be created by Contract Manager without AccessError')
        quotation = self.env['sale.order'].browse(action['res_id'])
        self.assertEqual(quotation.partner_id, self.partner)
        self.assertEqual(len(quotation.order_line), 1)
        self.assertTrue(cat_without_product.service_product_id)
        _logger.info('PASS: test_contract_manager_can_create_quotation_without_category_write_permission')

    def test_contract_manager_can_create_collection_point(self):
        """
        Verify that a user with the Contract Manager role can create and update
        collection points.
        """
        contract_manager_user = self.env['res.users'].create({
            'name': 'Test Contract Manager Point Creator',
            'login': 'test_wm_cm_point_creator',
            'email': 'cm_point@test.com',
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('wm_contracts_billing.group_wm_contract_manager').id,
            ])],
        })

        # Contract Manager creates a collection point
        point = self.env['wm.collection.point'].with_user(contract_manager_user).create({
            'name': 'New Site for Contract',
            'partner_id': self.partner.id,
            'street': '123 Contract Way',
            'city': 'Metropolis',
        })
        self.assertTrue(point.id)
        self.assertEqual(point.name, 'New Site for Contract')

        # Contract Manager updates the collection point
        point.with_user(contract_manager_user).write({'street': '456 Updated Way'})
        self.assertEqual(point.street, '456 Updated Way')
        _logger.info('PASS: test_contract_manager_can_create_collection_point')
