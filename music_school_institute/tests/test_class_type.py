# -*- coding: utf-8 -*-

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestClassType(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.student = cls.env['res.partner'].create({
            'name': 'Music Class Student',
            'student': True,
        })
        cls.second_student = cls.env['res.partner'].create({
            'name': 'Second Music Class Student',
            'student': True,
        })
        cls.teacher = cls.env['hr.employee'].create({
            'name': 'Music Teacher',
            'teacher': True,
        })
        cls.service = cls.env['service.type'].create({
            'name': 'Guitar Service',
            'instrument': 'Guitar',
            'teacher_id': cls.teacher.id,
        })
        account_domain = cls.env['account.account']._check_company_domain(cls.env.company)
        cls.income_account = cls.env['account.account'].search([
            *account_domain,
            ('account_type', '=', 'income'),
            ('deprecated', '=', False),
        ], limit=1)
        cls.sale_journal = cls.env['account.journal'].create({
            'name': 'Music School Sales Journal',
            'code': 'MSSJ',
            'type': 'sale',
            'company_id': cls.env.company.id,
        })
        cls.instrument = cls.env['product.product'].create({
            'name': 'Acoustic Guitar',
            'lst_price': 50.0,
            'music_instrument': True,
            'property_account_income_id': cls.income_account.id,
        })

    @classmethod
    def _create_class(cls, **values):
        defaults = {
            'name': 'Beginner Guitar',
            'from_date': '2026-05-04',
            'to_date': '2026-05-08',
            'service_id': cls.service.id,
            'instrument_id': cls.instrument.id,
            'teacher_id': cls.teacher.id,
            'student_ids': [Command.set(cls.student.ids)],
        }
        defaults.update(values)
        return cls.env['class.type'].create(defaults)

    def test_from_date_must_not_be_after_to_date(self):
        with self.assertRaises(ValidationError):
            self._create_class(
                from_date='2026-05-09',
                to_date='2026-05-08',
            )

    def test_compute_duration_counts_weekdays_between_dates(self):
        music_class = self._create_class(
            from_date='2026-05-01',
            to_date='2026-05-10',
        )

        self.assertEqual(music_class.duration, 6)

    def test_state_buttons_update_class_state(self):
        music_class = self._create_class()

        music_class.action_button_class_start()
        self.assertEqual(music_class.state, 'started')

        music_class.action_button_class_completed()
        self.assertEqual(music_class.state, 'completed')

        music_class.action_button_class_cancel()
        self.assertEqual(music_class.state, 'canceled')

        music_class.action_button_set_to_draft()
        self.assertEqual(music_class.state, 'draft')

    def test_action_button_create_order_creates_invoice_per_student(self):
        music_class = self._create_class(
            student_ids=[Command.set((self.student | self.second_student).ids)],
        )

        music_class.action_button_create_order()

        invoices = self.env['account.move'].search([
            ('class_id', '=', music_class.id),
        ])
        self.assertEqual(len(invoices), 2)
        self.assertEqual(music_class.state, 'invoice')
        self.assertEqual(set(invoices.mapped('partner_id').ids), set(music_class.student_ids.ids))
        self.assertEqual(invoices.invoice_line_ids.mapped('product_id'), self.instrument)

    def test_related_order_action_and_count_use_class_invoices(self):
        music_class = self._create_class()
        self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.student.id,
            'class_id': music_class.id,
            'journal_id': self.sale_journal.id,
            'invoice_date': music_class.from_date,
        })

        music_class._compute_order_count()
        action = music_class.action_related_order()

        self.assertEqual(music_class.order_count, 1)
        self.assertEqual(action['res_model'], 'account.move')
        self.assertEqual(action['domain'], [
            ('partner_id', 'in', music_class.student_ids.ids),
            ('class_id', '=', music_class.id),
        ])
