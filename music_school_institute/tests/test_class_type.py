# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError
from datetime import date, timedelta

@tagged('-at_install', 'post_install')
class TestClassType(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestClassType, cls).setUpClass()
        
        # Create required test data
        cls.student = cls.env['res.partner'].create({
            'name': 'Test Student',
            'student': True,
        })
        
        cls.teacher = cls.env['hr.employee'].create({
            'name': 'Test Teacher',
            'teacher': True,
        })
        
        cls.instrument = cls.env['product.product'].create({
            'name': 'Guitar',
            'music_instrument': True,
            'lst_price': 100.0,
        })
        
        cls.class_type = cls.env['class.type'].create({
            'name': 'Guitar Class',
            'from_date': date.today(),
            'to_date': date.today() + timedelta(days=10),
            'student_ids': [(4, cls.student.id)],
            'instrument_id': cls.instrument.id,
            'teacher_id': cls.teacher.id,
        })

    def test_01_compute_duration(self):
        """Test duration calculation (number of work days)."""
        # Trigger the compute method manually if needed, or check if computed
        self.class_type._compute_duration()
        self.assertTrue(self.class_type.duration > 0)

    def test_02_check_dates(self):
        """Test validation error for invalid dates."""
        with self.assertRaises(ValidationError):
            self.env['class.type'].create({
                'name': 'Invalid Date Class',
                'from_date': date.today() + timedelta(days=10),
                'to_date': date.today(),
                'student_ids': [(4, self.student.id)],
            })

    def test_03_action_buttons(self):
        """Test state transitions."""
        self.class_type.action_button_class_start()
        self.assertEqual(self.class_type.state, 'started')

        self.class_type.action_button_class_completed()
        self.assertEqual(self.class_type.state, 'completed')

        self.class_type.action_button_class_cancel()
        self.assertEqual(self.class_type.state, 'canceled')

        self.class_type.action_button_set_to_draft()
        self.assertEqual(self.class_type.state, 'draft')

    def test_04_create_order(self):
        """Test invoice creation."""
        self.class_type.action_button_create_order()
        self.assertEqual(self.class_type.state, 'invoice')
        
        # Check if an invoice is linked
        self.class_type._compute_order_count()
        self.assertTrue(self.class_type.order_count > 0, "Order count should be > 0 after creating an invoice.")
        
        # Check the smart button action
        action = self.class_type.related_order()
        self.assertEqual(action['res_model'], 'account.move')
        self.assertEqual(action['domain'], [('partner_id', 'in', self.class_type.student_ids.ids), ('class_id', '=', self.class_type.id)])
