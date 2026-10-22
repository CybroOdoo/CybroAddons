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
#############################################################################
from dateutil.relativedelta import relativedelta
from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase, new_test_user, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestInsuranceManagement(TransactionCase):
    """Tests the insurance, claim, agent and access rules of the module."""

    @classmethod
    def setUpClass(cls):
        """Create the shared partner, policy, agent and users."""
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Insurance Partner',
        })
        cls.policy_type = cls.env['policy.type'].create({
            'name': 'Health Policy Type',
        })
        cls.payment_type = cls.env['payment.type'].create({
            'name': 'Installment Type',
        })
        cls.policy = cls.env['policy.details'].create({
            'name': 'Gold Health Policy',
            'policy_type_id': cls.policy_type.id,
            'payment_type_ids': [(6, 0, [cls.payment_type.id])],
            'amount': 12000.0,
        })
        cls.agent_user = cls.env['res.users'].create({
            'name': 'Test Agent User',
            'login': 'agent_test_user@example.com',
            'email': 'agent_test_user@example.com',
        })
        cls.agent = cls.env['employee.details'].create({
            'name': 'Test Agent',
            'user_id': cls.agent_user.id,
            'phone': '1234567890',
            'salary_type': 'both',
            'base_salary': 3000.0,
        })
        # an insurance user without any accounting right and a manager
        cls.ins_user = new_test_user(
            cls.env, login='ins_user_test',
            groups='insurance_management_cybro.group_insurance_user')
        cls.ins_manager = new_test_user(
            cls.env, login='ins_manager_test',
            groups='insurance_management_cybro.group_insurance_manager')

    def test_01_insurance_flow(self):
        """Test sequence generation, invoice creation, and payment validation on closure."""
        insurance = self.env['insurance.details'].create({
            'partner_id': self.partner.id,
            'policy_id': self.policy.id,
            'employee_id': self.agent.id,
            'policy_duration': 12,
            'policy_number': 998877,
            'commission_rate': 10.0,
            'payment_type_id': self.payment_type.id,
        })
        self.assertNotEqual(insurance.name, 'New')
        self.assertEqual(insurance.amount_installment, 1000.0)

        insurance.action_confirm_insurance()
        self.assertEqual(insurance.state, 'confirmed')

        # Attempting to close unpaid insurance should raise UserError
        insurance.action_create_invoice()
        self.assertTrue(insurance.invoice_ids)

        with self.assertRaises(UserError):
            insurance.action_close_insurance()

    def test_02_agent_salary_payment(self):
        """Test agent salary and commission payment calculation."""
        self.env['insurance.details'].create({
            'partner_id': self.partner.id,
            'policy_id': self.policy.id,
            'employee_id': self.agent.id,
            'policy_duration': 12,
            'policy_number': 998878,
            'commission_rate': 10.0,
            'payment_type_id': self.payment_type.id,
            'start_date': fields.Date.today(),
        }).action_confirm_insurance()

        self.agent.action_salary_payment()
        self.assertTrue(self.agent.invoice_id)
        # Total salary: 3000 base + (10% of 12000) = 4200
        self.assertEqual(self.agent.invoice_id.invoice_line_ids.price_unit, 4200.0)

    def test_03_claim_details_flow(self):
        """Test insurance claim creation and bill generation."""
        insurance = self.env['insurance.details'].create({
            'partner_id': self.partner.id,
            'policy_id': self.policy.id,
            'employee_id': self.agent.id,
            'policy_duration': 12,
            'policy_number': 998879,
            'commission_rate': 10.0,
            'payment_type_id': self.payment_type.id,
        })
        insurance.action_confirm_insurance()

        claim = self.env['claim.details'].create({
            'insurance_id': insurance.id,
        })
        self.assertNotEqual(claim.name, 'New')
        self.assertEqual(claim.amount, 12000.0)

        claim.action_create_bill()
        self.assertTrue(claim.invoice_id)
        self.assertEqual(claim.invoice_id.move_type, 'in_invoice')

    def _create_insurance(self, number, **kwargs):
        """Create a draft insurance with the given policy number."""
        vals = {
            'partner_id': self.partner.id,
            'policy_id': self.policy.id,
            'employee_id': self.agent.id,
            'policy_duration': 12,
            'policy_number': number,
            'commission_rate': 10.0,
            'payment_type_id': self.payment_type.id,
        }
        vals.update(kwargs)
        return self.env['insurance.details'].create(vals)

    def _pay(self, invoice):
        """Post the invoice and register its full payment."""
        if invoice.state == 'draft':
            invoice.action_post()
        self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=invoice.ids,
        ).create({})._create_payments()

    def test_04_fixed_payment_invoices_full_amount(self):
        """A fixed payment type invoices the whole policy amount at once."""
        fixed = self.env.ref('insurance_management_cybro.payment_type_fixed')
        self.policy.payment_type_ids = [(4, fixed.id)]
        insurance = self._create_insurance(998880, payment_type_id=fixed.id)
        self.assertTrue(insurance.is_fixed_payment)
        insurance.action_confirm_insurance()
        insurance.action_create_invoice()
        self.assertEqual(insurance.invoice_ids.amount_total, 12000.0)
        with self.assertRaises(ValidationError):
            insurance.action_create_invoice()

    def test_05_installments_stop_when_fully_invoiced(self):
        insurance = self._create_insurance(998881, policy_duration=2)
        insurance.action_confirm_insurance()
        insurance.action_create_invoice()
        insurance.action_create_invoice()
        self.assertEqual(insurance.amount_remaining, 0.0)
        with self.assertRaises(ValidationError):
            insurance.action_create_invoice()

    def test_06_successful_close_after_payment(self):
        insurance = self._create_insurance(998882, policy_duration=1)
        insurance.action_confirm_insurance()
        insurance.action_create_invoice()
        self._pay(insurance.invoice_ids)
        insurance.action_close_insurance()
        self.assertEqual(insurance.state, 'closed')
        self.assertEqual(insurance.close_date, fields.Date.today())

    def test_07_confirm_requires_positive_amount(self):
        self.policy.amount = 0.0
        insurance = self._create_insurance(998883)
        with self.assertRaises(UserError):
            insurance.action_confirm_insurance()

    def test_08_commission_rate_is_a_plain_percentage(self):
        """The rate is stored as entered (10 means 10%), within 0-100."""
        self.assertEqual(self._create_insurance(998884, commission_rate=0.0).commission_rate, 0.0)
        self._create_insurance(998885, commission_rate=100.0)
        for bad in (-1.0, 100.5):
            with self.assertRaises(ValidationError):
                self._create_insurance(998886, commission_rate=bad)

    def test_09_actions_require_a_single_record(self):
        first = self._create_insurance(998887)
        second = self._create_insurance(998888)
        both = first | second
        for method in ('action_confirm_insurance', 'action_create_invoice', 'action_close_insurance'):
            with self.assertRaises(ValueError):
                getattr(both, method)()
        with self.assertRaises(ValueError):
            (self.agent | self.agent.copy({'name': 'Other'})).action_salary_payment()

    def test_10_salary_types_and_validations(self):
        self.agent.salary_type = 'fixed'
        self.agent.action_salary_payment()
        self.assertEqual(self.agent.invoice_id.invoice_line_ids.price_unit, 3000.0)
        # the previous draft payment must be validated first
        with self.assertRaises(UserError):
            self.agent.action_salary_payment()
        commission_agent = self.agent.copy({
            'name': 'Commission Agent', 'salary_type': 'commission',
            'user_id': self.agent_user.id})
        with self.assertRaises(UserError):
            commission_agent.action_salary_payment()  # no insurance, so nothing to pay
        self._create_insurance(
            998889, employee_id=commission_agent.id,
        ).action_confirm_insurance()
        commission_agent.action_salary_payment()
        self.assertEqual(commission_agent.invoice_id.invoice_line_ids.price_unit, 1200.0)

    def test_11_phone_validation(self):
        with self.assertRaises(ValidationError):
            self.agent.phone = '12345'

    def _confirmed_insurance(self, number, **kwargs):
        """Create and confirm an insurance."""
        insurance = self._create_insurance(number, **kwargs)
        insurance.action_confirm_insurance()
        return insurance

    def test_12_invoice_requires_confirmed_state(self):
        insurance = self._create_insurance(998890)
        self.assertFalse(insurance.can_create_invoice)
        with self.assertRaises(UserError):
            insurance.action_create_invoice()
        insurance.action_confirm_insurance()
        self.assertTrue(insurance.can_create_invoice)
        with self.assertRaises(UserError):
            insurance.action_confirm_insurance()

    def test_13_invoice_currency_and_company(self):
        insurance = self._confirmed_insurance(998891)
        self.assertEqual(insurance.currency_id, self.policy.currency_id)
        action = insurance.action_create_invoice()
        invoice = insurance.invoice_ids
        self.assertEqual(action['res_id'], invoice.id)
        self.assertEqual(invoice.currency_id, insurance.currency_id)
        self.assertEqual(invoice.company_id, insurance.company_id)
        self.assertEqual(invoice.insurance_id, insurance)

    def test_14_cancelled_invoice_is_not_counted(self):
        insurance = self._confirmed_insurance(998892, policy_duration=1)
        insurance.action_create_invoice()
        self.assertEqual(insurance.amount_remaining, 0.0)
        self.assertFalse(insurance.can_create_invoice)
        insurance.invoice_ids.button_cancel()
        self.assertEqual(insurance.amount_remaining, 12000.0)
        self.assertTrue(insurance.can_create_invoice)
        insurance.action_create_invoice()
        self.assertEqual(len(insurance.invoice_ids), 2)

    def test_15_last_installment_settles_the_rounding(self):
        self.policy.amount = 100.0
        insurance = self._confirmed_insurance(998893, policy_duration=3)
        for _i in range(3):
            insurance.action_create_invoice()
        self.assertEqual(
            sorted(insurance.invoice_ids.mapped('amount_total')),
            [33.33, 33.33, 33.34])
        self.assertEqual(insurance.amount_remaining, 0.0)

    def test_16_close_requires_fully_invoiced_and_paid(self):
        insurance = self._create_insurance(998894)
        with self.assertRaises(UserError):
            insurance.action_close_insurance()  # not confirmed
        insurance.action_confirm_insurance()
        with self.assertRaises(UserError):
            insurance.action_close_insurance()  # no invoice at all
        insurance.action_create_invoice()
        self._pay(insurance.invoice_ids)
        with self.assertRaises(UserError):
            insurance.action_close_insurance()  # only partly invoiced

    def test_17_policy_number_is_unique_per_company(self):
        self._create_insurance(998895)
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'), \
                self.cr.savepoint():
            self._create_insurance(998895)
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'), \
                self.cr.savepoint():
            self._create_insurance(0)

    def test_18_confirmed_insurance_cannot_be_deleted(self):
        insurance = self._confirmed_insurance(998896)
        with self.assertRaises(UserError):
            insurance.unlink()
        self._create_insurance(998897).unlink()

    def test_19_claim_rules(self):
        claim = self.env['claim.details'].create({
            'insurance_id': self._confirmed_insurance(998899).id,
            'amount': 5000.0,
        })
        action = claim.action_create_bill()
        self.assertEqual(action['res_id'], claim.invoice_id.id)
        self.assertEqual(claim.invoice_id.amount_total, 5000.0)
        self.assertEqual(claim.invoice_id.currency_id, claim.currency_id)
        self.assertEqual(claim.invoice_id.claim_id, claim)
        self.assertFalse(claim.can_create_bill)
        with self.assertRaises(UserError):
            claim.action_create_bill()
        with self.assertRaises(UserError):
            claim.unlink()
        # a cancelled bill can be generated again
        claim.invoice_id.button_cancel()
        self.assertTrue(claim.can_create_bill)
        claim.action_create_bill()

    def test_20_claims_cannot_exceed_the_insured_amount(self):
        insurance = self._confirmed_insurance(998900)
        first = self.env['claim.details'].create({
            'insurance_id': insurance.id, 'amount': 5000.0})
        second = self.env['claim.details'].create({'insurance_id': insurance.id})
        self.assertEqual(second.amount, 7000.0)
        with self.assertRaises(ValidationError):
            first.amount = 5001.0
        with self.assertRaises(ValidationError):
            self.env['claim.details'].create({'insurance_id': insurance.id})

    def test_21_claim_bill_requires_confirmed_insurance(self):
        insurance = self._confirmed_insurance(998901)
        claim = self.env['claim.details'].create({'insurance_id': insurance.id})
        insurance.state = 'draft'
        with self.assertRaises(UserError):
            claim.action_create_bill()

    def test_22_salary_requires_user_and_counts_confirmed_only(self):
        agent = self.agent.copy({
            'name': 'Commission Agent', 'salary_type': 'commission',
            'user_id': self.agent_user.id})
        self._create_insurance(998902, employee_id=agent.id)  # draft
        with self.assertRaises(UserError):
            agent.action_salary_payment()  # nothing confirmed to pay
        self._confirmed_insurance(998903, employee_id=agent.id)
        agent.user_id = False
        with self.assertRaises(UserError):
            agent.action_salary_payment()
        agent.user_id = self.agent_user
        agent.action_salary_payment()
        self.assertEqual(agent.invoice_id.currency_id, agent.currency_id)
        self.assertEqual(agent.invoice_id.invoice_line_ids.price_unit, 1200.0)

    def test_23_salary_period_rules(self):
        agent = self.agent.copy({
            'name': 'Both Agent', 'salary_type': 'both',
            'user_id': self.agent_user.id})
        self._confirmed_insurance(998904, employee_id=agent.id)
        agent.action_salary_payment()
        bill = agent.invoice_id
        self.assertEqual(bill.invoice_line_ids.price_unit, 4200.0)
        bill.action_post()
        # already paid for today, so neither the salary nor the commission
        # of the same insurance is paid twice
        with self.assertRaises(UserError):
            agent.action_salary_payment()
        # a cancelled payment does not consume the period
        bill.button_draft()
        bill.button_cancel()
        agent.action_salary_payment()
        self.assertEqual(agent.invoice_id.invoice_line_ids.price_unit, 4200.0)
        # commission only counts insurances started after the last payment
        agent.invoice_id.action_post()
        agent.last_salary_date = (
            fields.Date.today() - relativedelta(days=1))
        self.assertEqual(agent._get_commission(agent.last_salary_date,
                                               fields.Date.today()), 1200.0)
        self.assertEqual(agent._get_commission(fields.Date.today(),
                                               fields.Date.today()), 0.0)

    def test_24_phone_formats(self):
        for phone in ('+91 98765 43210', '98765-43210', '9876543210'):
            self.agent.phone = phone
        for phone in ('abc1234567', '12345', '+', '12 34'):
            with self.assertRaises(ValidationError):
                self.agent.phone = phone

    def test_25_insurance_user_cannot_bill(self):
        """Users without accounting rights cannot create invoices or bills,
        neither directly nor through the actions."""
        insurance = self._confirmed_insurance(998905)
        claim = self.env['claim.details'].create({'insurance_id': insurance.id})
        as_user = self.ins_user
        with self.assertRaises(AccessError):
            insurance.with_user(as_user).action_create_invoice()
        with self.assertRaises(AccessError):
            claim.with_user(as_user).action_create_bill()
        with self.assertRaises(AccessError):
            self.agent.with_user(as_user).action_salary_payment()
        self.assertFalse(insurance.invoice_ids | claim.invoice_id)
        # the manager implies the invoicing right
        insurance.with_user(self.ins_manager).action_create_invoice()
        claim.with_user(self.ins_manager).action_create_bill()
        self.assertTrue(insurance.invoice_ids and claim.invoice_id)

    def test_26_insurance_user_access_rights(self):
        user_env = self.env(user=self.ins_user)
        insurance = user_env['insurance.details'].create({
            'partner_id': self.partner.id,
            'policy_id': self.policy.id,
            'employee_id': self.agent.id,
            'policy_duration': 12,
            'policy_number': 998906,
            'payment_type_id': self.payment_type.id,
        })
        insurance.action_confirm_insurance()
        claim = user_env['claim.details'].create({'insurance_id': insurance.id})
        self.assertFalse(claim.has_bill)
        # Verify form view can be loaded by an Insurance User without view validation error
        self.env['claim.details'].with_user(self.ins_user).get_views(
            [(self.env.ref('insurance_management_cybro.claim_details_view_form').id, 'form')])
        self.assertEqual(user_env['policy.details'].browse(
            self.policy.id).amount, 12000.0)
        # master data and agents cannot be changed by plain users
        with self.assertRaises(AccessError):
            user_env['policy.details'].browse(self.policy.id).amount = 1.0
        with self.assertRaises(AccessError):
            user_env['policy.type'].create({'name': 'Nope'})
        with self.assertRaises(AccessError):
            user_env['payment.type'].create({'name': 'Nope'})
        with self.assertRaises(AccessError):
            user_env['employee.details'].browse(self.agent.id).name = 'Nope'
        # salary data is reserved to managers
        agent = user_env['employee.details'].browse(self.agent.id)
        self.assertEqual(agent.name, 'Test Agent')
        with self.assertRaises(AccessError):
            agent.base_salary
        with self.assertRaises(AccessError):
            user_env['insurance.details'].browse(insurance.id).unlink()
        manager_env = self.env(user=self.ins_manager)
        manager_env['policy.type'].create({'name': 'Allowed'})
        self.assertEqual(
            manager_env['employee.details'].browse(self.agent.id).base_salary,
            3000.0)

    def test_27_system_payment_types_are_protected(self):
        for xmlid in ('payment_type_fixed', 'payment_type_installment'):
            payment_type = self.env.ref(f'insurance_management_cybro.{xmlid}')
            with self.assertRaises(UserError):
                payment_type.with_user(self.ins_manager).unlink()
        self.payment_type.with_user(self.ins_manager).unlink()

    def test_28_multi_company(self):
        company = self.env['res.company'].create({'name': 'Other Insurer'})
        policy = self.policy.copy({'company_id': company.id})
        agent = self.agent.copy({'company_id': company.id})
        other = self.env['insurance.details'].create({
            'partner_id': self.partner.id,
            'policy_id': policy.id,
            'employee_id': agent.id,
            'company_id': company.id,
            'policy_duration': 12,
            'policy_number': 998907,
        })
        mine = self._create_insurance(998908)
        user_env = self.env(user=self.ins_manager)
        found = user_env['insurance.details'].search(
            [('id', 'in', (other | mine).ids)])
        self.assertEqual(found, mine)
        self.assertFalse(user_env['policy.details'].search(
            [('id', '=', policy.id)]))
        # records of two companies cannot be mixed
        with self.assertRaises(UserError):
            self._create_insurance(998909, policy_id=policy.id)
