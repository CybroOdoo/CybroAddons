# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestManpowerSupplyManagement(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.customer = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })

        cls.skill = cls.env['skill.details'].create({
            'name': 'Welder',
        })

        cls.worker1 = cls.env['workers.details'].create({
            'name': 'Worker 1',
            'phone_number': '9876543210',
            'email': 'worker1@test.com',
            'image_worker': False,
            'rate': 100,
            'wage': 50,
            'skill_ids': [(6, 0, [cls.skill.id])],
        })

        cls.worker2 = cls.env['workers.details'].create({
            'name': 'Worker 2',
            'phone_number': '9876543211',
            'email': 'worker2@test.com',
            'image_worker': False,
            'rate': 120,
            'wage': 60,
            'skill_ids': [(6, 0, [cls.skill.id])],
        })
    def _create_contract(self):
        return self.env['labour.supply'].create({
            'customer_id': self.customer.id,
            'skill_ids': [(0, 0, {
                'skill_id': self.skill.id,
                'number_of_labour_required': 1,
                'from_date': date.today() + timedelta(days=5),
                'to_date': date.today() + timedelta(days=10),
            })]
        })

    def test_skill_creation(self):
        self.assertEqual(self.skill.name, 'Welder')

    def test_worker_partner_created(self):
        self.assertTrue(self.worker1.related_partner_id)

    def test_worker_default_state(self):
        self.assertEqual(self.worker1.state, 'available')

    def test_contract_sequence_generated(self):
        contract = self._create_contract()

        self.assertTrue(contract.sequence_number)
        self.assertNotEqual(contract.sequence_number, 'New')

    def test_action_fetch_assigns_workers(self):
        contract = self._create_contract()

        contract.action_fetch()

        self.assertTrue(contract.workers_ids)
        self.assertEqual(contract.state, 'ready')

    def test_action_fetch_calculates_amount(self):
        contract = self._create_contract()

        contract.action_fetch()

        self.assertGreater(contract.total_amount, 0)

    def test_action_fetch_sets_dates(self):
        contract = self._create_contract()

        contract.action_fetch()

        self.assertTrue(contract.from_date)
        self.assertTrue(contract.to_date)

    def test_action_fetch_without_skill_raises(self):
        contract = self.env['labour.supply'].create({
            'customer_id': self.customer.id,
        })

        with self.assertRaises(ValidationError):
            contract.action_fetch()

    def test_action_fetch_invalid_date_range(self):
        contract = self.env['labour.supply'].create({
            'customer_id': self.customer.id,
            'skill_ids': [(0, 0, {
                'skill_id': self.skill.id,
                'number_of_labour_required': 1,
                'from_date': date.today() + timedelta(days=10),
                'to_date': date.today() + timedelta(days=5),
            })]
        })

        with self.assertRaises(ValidationError):
            contract.action_fetch()

    def test_action_confirm(self):
        contract = self._create_contract()

        contract.action_confirm()

        self.assertEqual(contract.state, 'confirmed')

    def test_action_draft(self):
        contract = self._create_contract()

        contract.action_fetch()
        contract.action_draft()

        self.assertEqual(contract.state, 'draft')
        self.assertFalse(contract.workers_ids)

    def test_action_cancel(self):
        contract = self._create_contract()

        contract.action_fetch()
        contract.action_cancel()

        self.assertEqual(contract.state, 'canceled')

    def test_action_create_invoice(self):
        contract = self._create_contract()

        contract.action_fetch()

        action = contract.action_create_invoice()

        self.assertEqual(contract.state, 'invoiced')
        self.assertTrue(contract.invoice_id)

        self.assertEqual(
            action.get('res_model'),
            'account.move'
        )

    def test_action_labour_supply_invoices(self):
        contract = self._create_contract()

        result = contract.action_labour_supply_invoices()

        self.assertEqual(
            result.get('res_model'),
            'account.move'
        )

    def test_cron_change_state_expired(self):
        contract = self._create_contract()

        contract.write({
            'state': 'invoiced',
            'from_date': date.today() - timedelta(days=10),
            'to_date': date.today() - timedelta(days=1),
        })

        contract.cron_change_state()

        self.assertEqual(contract.state, 'expired')
        