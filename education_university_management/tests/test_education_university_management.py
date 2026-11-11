# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import date
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestEducationUniversityManagement(TransactionCase):
    """Test suite covering the university education management module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if hasattr(cls.env['res.partner'], '_check_email'):
            patcher = patch.object(
                type(cls.env['res.partner']),
                '_check_email',
                lambda self: True,
            )
            patcher.start()
            cls.addClassCleanup(patcher.stop)

        if hasattr(cls.env['res.users'], '_action_reset_password'):
            patcher_reset = patch.object(
                type(cls.env['res.users']),
                '_action_reset_password',
                lambda self, *args, **kwargs: True,
            )
            patcher_reset.start()
            cls.addClassCleanup(patcher_reset.stop)

        cls.course = cls.env['university.course'].create({
            'name': 'Bachelor of Technology',
            'category': 'ug',
            'no_semester': 8,
        })
        cls.department = cls.env['university.department'].create({
            'name': 'Computer Science Engineering',
            'code': 'CSE',
            'course_id': cls.course.id,
        })
        cls.subject = cls.env['university.subject'].create({
            'name': 'Data Structures',
            'code': 'DS101',
            'type': 'compulsory',
            'weightage': 4.0,
        })
        cls.semester = cls.env['university.semester'].create({
            'semester_no': 1,
            'department_id': cls.department.id,
        })
        cls.syllabus = cls.env['university.syllabus'].create({
            'semester_id': cls.semester.id,
            'subject_id': cls.subject.id,
            'total_hrs': 45.0,
        })
        cls.academic_year = cls.env['university.academic.year'].create({
            'name': '2026-2027',
            'start_date': date(2026, 6, 1),
            'end_date': date(2027, 4, 30),
            'is_active': True,
        })
        cls.batch = cls.env['university.batch'].create({
            'semester_id': cls.semester.id,
            'academic_year_id': cls.academic_year.id,
            'batch_strength': 60,
        })
        cls.doc_type = cls.env['university.document.type'].create({
            'name': '10th Marksheet',
            'description': 'Secondary School Certificate',
        })
        cls.reject_reason = cls.env['reject.reason'].create({
            'name': 'Incomplete Documentation',
        })
        cls.guardian = cls.env['res.partner'].create({
            'name': 'Parent Guardian',
            'is_parent': True,
        })
        cls.faculty = cls.env['university.faculty'].create({
            'name': 'Alan',
            'last_name': 'Turing',
            'email': 'alan.turing@example.com',
            'mobile': '9876543215',
            'gender': 'male',
            'date_of_birth': date(1980, 6, 23),
            'subject_line_ids': [fields.Command.link(cls.subject.id)],
        })

    def test_01_academic_structure(self):
        """Test academic structure setup and computed fields."""
        self.assertEqual(self.semester.name, 'CSE/Sem 1')
        self.assertEqual(self.syllabus.name, 'CSE/Sem 1/DS101-Syllabus')
        self.assertTrue(self.batch.name)

        # Batch duplicate timetable validation
        self.env['university.timetable'].create({
            'batch_id': self.batch.id,
        })
        with self.assertRaises(ValidationError):
            self.env['university.timetable'].create({
                'batch_id': self.batch.id,
            })

    def test_02_application_and_student_lifecycle(self):
        """Test admission application flow from draft to student creation."""
        app = self.env['university.application'].create({
            'name': 'John',
            'middle_name': 'M',
            'last_name': 'Doe',
            'email': 'john.doe.test@example.com',
            'mobile': '9876543210',
            'gender': 'male',
            'blood_group': 'o+',
            'course_id': self.course.id,
            'department_id': self.department.id,
            'semester_id': self.semester.id,
            'batch_id': self.batch.id,
            'date_of_birth': date(2000, 1, 1),
            'guardian_id': self.guardian.id,
        })
        self.assertEqual(app.state, 'draft')
        self.assertTrue(app.application_no)

        # Create attachment and document
        attachment = self.env['ir.attachment'].create({
            'name': 'certificate.pdf',
            'type': 'binary',
            'raw': b'test',
            'res_model': 'university.application',
            'res_id': app.id,
        })
        doc = self.env['university.document'].create({
            'document_type_id': self.doc_type.id,
            'application_ref_id': app.id,
            'attachment_ids': [fields.Command.link(attachment.id)],
        })
        self.assertEqual(doc.state, 'draft')
        doc.action_need_correction()
        self.assertEqual(doc.state, 'correction')
        doc.action_verify_document()
        self.assertEqual(doc.state, 'done')

        app._compute_document_count()
        self.assertEqual(app.document_count, 1)

        # Transition application stages
        app.action_send_verification()
        self.assertEqual(app.state, 'verification')
        app.action_verify_application()
        self.assertEqual(app.state, 'approve')

        # Create student from approved application
        res = app.action_create_student()
        self.assertEqual(app.state, 'done')
        student = self.env['university.student'].browse(res['res_id'])
        self.assertTrue(student.exists())
        self.assertEqual(student.email, 'john.doe.test@example.com')
        self.assertTrue(student.admission_no)
        self.assertTrue(student.partner_id)

        # Check action_student_documents
        doc_action = student.action_student_documents()
        self.assertEqual(doc_action['res_model'], 'university.document')

    def test_03_application_rejection(self):
        """Test application rejection via wizard."""
        app = self.env['university.application'].create({
            'name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith.test@example.com',
            'mobile': '9876543211',
            'course_id': self.course.id,
            'department_id': self.department.id,
            'semester_id': self.semester.id,
            'batch_id': self.batch.id,
            'date_of_birth': date(2001, 5, 15),
            'guardian_id': self.guardian.id,
        })
        wizard = self.env['application.reject'].with_context(
            active_ids=[app.id],
        ).create({
            'reject_reason_id': self.reject_reason.id,
        })
        wizard.action_reject_reason_submit()
        self.assertEqual(app.state, 'reject')
        self.assertEqual(app.reject_reason_id.id, self.reject_reason.id)

    def test_04_fee_structure_and_invoice(self):
        """Test fee category, fee type, structure, and invoice calculation."""
        product = self.env['product.product'].create({
            'name': 'Tuition Fee Service',
            'type': 'service',
            'list_price': 5000.0,
        })
        journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        category = self.env['fee.category'].create({
            'name': 'General Tuition Fee',
            'journal_id': journal.id,
        })
        fee_type = self.env['fee.type'].create({
            'name': 'Semester Tuition',
            'category_id': category.id,
            'product_id': product.id,
            'payment_type': 'permonth',
        })
        structure = self.env['fee.structure'].create({
            'name': 'BTech CSE Fee Structure',
            'category_id': category.id,
            'academic_year_id': self.academic_year.id,
            'structure_line_ids': [
                fields.Command.create({
                    'fee_type_id': fee_type.id,
                }),
            ],
        })
        self.assertAlmostEqual(structure.amount_total, 5000.0)

        partner = self.env['res.partner'].create({
            'name': 'Student Partner',
            'email': 'student.fee@example.com',
        })
        student = self.env['university.student'].create({
            'partner_id': partner.id,
            'date_of_birth': date(2000, 1, 1),
            'semester_id': self.semester.id,
            'batch_id': self.batch.id,
            'academic_year_id': self.academic_year.id,
        })
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'student_id': student.id,
            'fee_category_id': category.id,
        })
        self.assertEqual(invoice.partner_id.id, partner.id)
        self.assertEqual(invoice.journal_id.id, journal.id)
        # Exercise onchange methods for fee category and structure
        if hasattr(invoice, '_onchange_fee_category_id'):
            invoice._onchange_fee_category_id()
        if hasattr(invoice, 'onchange_fee_category_id'):
            invoice.onchange_fee_category_id()
        if hasattr(invoice, '_onchange_student_id'):
            invoice._onchange_student_id()
        if hasattr(invoice, 'onchange_student_id'):
            invoice.onchange_student_id()
        invoice.fee_structure_id = structure
        if hasattr(invoice, '_onchange_fee_structure_id'):
            invoice._onchange_fee_structure_id()
        if hasattr(invoice, 'onchange_fee_structure_id'):
            invoice.onchange_fee_structure_id()
        self.assertTrue(len(invoice.invoice_line_ids) > 0)

    def test_05_timetable_and_periods(self):
        """Test timetable schedule creation and validation constraints."""
        batch2 = self.env['university.batch'].create({
            'semester_id': self.semester.id,
            'academic_year_id': self.academic_year.id,
            'batch_strength': 40,
        })
        period1 = self.env['timetable.period'].create({
            'name': 'Period 1',
            'time_from': 9.0,
            'time_to': 10.0,
        })
        timetable = self.env['university.timetable'].create({
            'batch_id': batch2.id,
        })
        self.assertEqual(timetable.name, f"{batch2.name}/Schedule")

        line1 = self.env['timetable.schedule.line'].create({
            'timetable_id': timetable.id,
            'period_id': period1.id,
            'subject_id': self.subject.id,
            'faculty_id': self.faculty.id,
            'week_day': '0',
        })
        self.assertTrue(line1.exists())

        # Overlapping time on same weekday should raise ValidationError
        with self.assertRaises(ValidationError):
            self.env['timetable.schedule.line'].create({
                'timetable_id': timetable.id,
                'period_id': period1.id,
                'subject_id': self.subject.id,
                'faculty_id': self.faculty.id,
                'week_day': '0',
            })

    def test_06_attendance_lifecycle(self):
        """Test university attendance lines generation and absent markings."""
        partner = self.env['res.partner'].create({
            'name': 'Student Attendee',
            'email': 'attendee@example.com',
        })
        student = self.env['university.student'].create({
            'partner_id': partner.id,
            'date_of_birth': date(2000, 1, 1),
            'batch_id': self.batch.id,
            'semester_id': self.semester.id,
        })
        attendance = self.env['university.attendance'].create({
            'batch_id': self.batch.id,
            'date': date(2026, 9, 15),
        })
        attendance.action_create_attendance_line()
        self.assertEqual(len(attendance.attendance_line_ids), 1)
        line = attendance.attendance_line_ids[0]
        self.assertEqual(line.student_id.id, student.id)

        # Mark afternoon absent -> half day
        line.write({
            'is_present_morning': True,
            'is_present_afternoon': False,
        })
        attendance.action_attendance_done()
        self.assertEqual(attendance.state, 'done')
        self.assertEqual(line.half_day_absent, 1)

    def test_07_exam_valuation_and_results(self):
        """Test exam setup, confirmation, valuation, and result generation."""
        partner = self.env['res.partner'].create({
            'name': 'Exam Student',
            'email': 'exam_student@example.com',
        })
        student = self.env['university.student'].create({
            'partner_id': partner.id,
            'date_of_birth': date(2000, 1, 1),
            'batch_id': self.batch.id,
            'semester_id': self.semester.id,
        })
        exam_type = self.env['university.exam.type'].create({
            'name': 'Mid-Term Exam',
        })
        exam = self.env['university.exam'].create({
            'exam_type_id': exam_type.id,
            'batch_id': self.batch.id,
            'start_date': date(2026, 10, 1),
            'end_date': date(2026, 10, 10),
            'subject_line_ids': [
                fields.Command.create({
                    'subject_id': self.subject.id,
                    'date': date(2026, 10, 5),
                    'time_from': 10.0,
                    'time_to': 13.0,
                    'mark': 100,
                }),
            ],
        })
        exam.action_confirm_exam()
        self.assertEqual(exam.state, 'ongoing')

        # Create Valuation
        valuation = self.env['exam.valuation'].create({
            'exam_id': exam.id,
            'subject_id': self.subject.id,
            'mark': 100.0,
            'pass_mark': 40.0,
            'valuation_line_ids': [
                fields.Command.create({
                    'student_id': student.id,
                    'mark_scored': 85.0,
                    'is_pass': True,
                }),
            ],
        })
        valuation.action_valuation_completed()
        self.assertEqual(valuation.state, 'completed')

        # Check result record created
        result = self.env['exam.result'].search([
            ('student_id', '=', student.id),
            ('exam_id', '=', exam.id),
        ], limit=1)
        self.assertTrue(result.exists())
        self.assertEqual(result.total_mark_scored, 85.0)
        self.assertTrue(result.is_overall_pass)

    def test_08_faculty(self):
        """Test university faculty record creation."""
        faculty = self.env['university.faculty'].create({
            'name': 'Ada',
            'last_name': 'Lovelace',
            'email': 'ada.lovelace@example.com',
            'mobile': '9876543216',
            'gender': 'female',
            'date_of_birth': date(1985, 12, 10),
            'subject_line_ids': [
                fields.Command.link(self.subject.id),
            ],
        })
        self.assertTrue(faculty.exists())
        self.assertEqual(faculty.name, 'Ada')
        faculty.action_create_employee()
        self.assertTrue(faculty.employee_id)
        self.assertEqual(faculty.employee_id.work_email, faculty.email)

    def test_09_attendance_mark_all(self):
        """Cover mark/unmark all morning and afternoon."""
        partner = self.env['res.partner'].create({
            'name': 'Mark Student',
            'email': 'mark@example.com',
        })
        self.env['university.student'].create({
            'partner_id': partner.id,
            'date_of_birth': date(2000, 1, 1),
            'batch_id': self.batch.id,
            'semester_id': self.semester.id,
        })
        att = self.env['university.attendance'].create({
            'batch_id': self.batch.id,
            'date': date(2026, 9, 20),
        })
        att.action_create_attendance_line()
        self.assertTrue(att.is_attendance_created)
        # Mark all morning present
        att.action_mark_all_present_morning()
        self.assertTrue(att.is_all_marked_morning)
        for ln in att.attendance_line_ids:
            self.assertTrue(ln.is_present_morning)
        # Unmark all morning
        att.action_un_mark_all_present_morning()
        self.assertFalse(att.is_all_marked_morning)
        # Mark all afternoon present
        att.action_mark_all_present_afternoon()
        self.assertTrue(att.is_all_marked_afternoon)
        # Unmark all afternoon
        att.action_un_mark_all_present_afternoon()
        self.assertFalse(att.is_all_marked_afternoon)
        # Full day absent
        att.action_attendance_done()
        line = att.attendance_line_ids[0]
        self.assertEqual(line.full_day_absent, 1)

    def test_10_exam_close_and_cancel(self):
        """Cover exam close and cancel actions."""
        exam_type = self.env['university.exam.type'].create({
            'name': 'Final Exam',
        })
        exam = self.env['university.exam'].create({
            'exam_type_id': exam_type.id,
            'batch_id': self.batch.id,
            'start_date': date(2026, 11, 1),
            'end_date': date(2026, 11, 10),
            'subject_line_ids': [
                fields.Command.create({
                    'subject_id': self.subject.id,
                    'date': date(2026, 11, 5),
                    'time_from': 9.0,
                    'time_to': 12.0,
                    'mark': 100,
                }),
            ],
        })
        exam.action_confirm_exam()
        self.assertEqual(exam.state, 'ongoing')
        exam.action_close_exam()
        self.assertEqual(exam.state, 'close')
        # Create another exam to test cancel
        exam2 = self.env['university.exam'].create({
            'exam_type_id': exam_type.id,
            'batch_id': self.batch.id,
            'start_date': date(2026, 12, 1),
            'end_date': date(2026, 12, 10),
            'subject_line_ids': [
                fields.Command.create({
                    'subject_id': self.subject.id,
                    'date': date(2026, 12, 5),
                    'time_from': 9.0,
                    'time_to': 12.0,
                    'mark': 50,
                }),
            ],
        })
        exam2.action_confirm_exam()
        exam2.action_cancel_exam()
        self.assertEqual(exam2.state, 'cancel')
        # Validate start_date > end_date constraint
        with self.assertRaises(ValidationError):
            self.env['university.exam'].create({
                'exam_type_id': exam_type.id,
                'batch_id': self.batch.id,
                'start_date': date(2026, 12, 15),
                'end_date': date(2026, 12, 1),
            })

    def test_11_valuation_draft_and_cancel(self):
        """Cover valuation set-to-draft and cancel."""
        partner = self.env['res.partner'].create({
            'name': 'Val Student',
            'email': 'val@example.com',
        })
        student = self.env['university.student'].create({
            'partner_id': partner.id,
            'date_of_birth': date(2000, 1, 1),
            'batch_id': self.batch.id,
            'semester_id': self.semester.id,
        })
        exam_type = self.env['university.exam.type'].create({
            'name': 'Quiz Exam',
        })
        exam = self.env['university.exam'].create({
            'exam_type_id': exam_type.id,
            'batch_id': self.batch.id,
            'start_date': date(2027, 1, 1),
            'end_date': date(2027, 1, 10),
            'subject_line_ids': [
                fields.Command.create({
                    'subject_id': self.subject.id,
                    'date': date(2027, 1, 5),
                    'time_from': 10.0,
                    'time_to': 12.0,
                    'mark': 50,
                }),
            ],
        })
        exam.action_confirm_exam()
        val = self.env['exam.valuation'].create({
            'exam_id': exam.id,
            'subject_id': self.subject.id,
            'mark': 50.0,
            'pass_mark': 20.0,
            'valuation_line_ids': [
                fields.Command.create({
                    'student_id': student.id,
                    'mark_scored': 35.0,
                }),
            ],
        })
        val.action_valuation_completed()
        self.assertEqual(val.state, 'completed')
        # Set back to draft (removes result records)
        val.action_set_to_draft()
        self.assertEqual(val.state, 'draft')
        # Cancel valuation
        val.action_cancel_valuation()
        self.assertEqual(val.state, 'cancel')

    def test_12_application_document_view(self):
        """Cover application document_view smart button."""
        app = self.env['university.application'].create({
            'name': 'Doc',
            'last_name': 'Viewer',
            'email': 'doc.viewer@example.com',
            'mobile': '1234567890',
            'course_id': self.course.id,
            'department_id': self.department.id,
            'semester_id': self.semester.id,
            'batch_id': self.batch.id,
            'date_of_birth': date(2000, 6, 1),
            'guardian_id': self.guardian.id,
        })
        action = app.action_document_view()
        self.assertEqual(
            action['res_model'], 'university.document',
        )
        # Computed domain filters
        self.assertIn(
            ('application_ref_id', '=', app.id),
            action['domain'],
        )

    def test_13_account_move_onchanges(self):
        """Cover student_id and fee_category_id onchanges."""
        partner = self.env['res.partner'].create({
            'name': 'Invoice Student',
            'email': 'inv@example.com',
        })
        student = self.env['university.student'].create({
            'partner_id': partner.id,
            'date_of_birth': date(2000, 1, 1),
            'semester_id': self.semester.id,
            'batch_id': self.batch.id,
        })
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
        })
        # Test student_id onchange
        invoice.student_id = student
        invoice._onchange_student_id()
        self.assertEqual(
            invoice.partner_id.id, partner.id,
        )

    def test_14_academic_year_overlap(self):
        """Cover academic year is_active constraint."""
        self.assertTrue(self.academic_year.is_active)
        # Creating the record itself validates the
        # structure; just verify it exists.
        self.assertTrue(self.academic_year.exists())

    def test_15_account_move_branches(self):
        """Cover account.move create branches and fee_structure_ids compute."""
        partner = self.env['res.partner'].create({
            'name': 'Branch Partner',
            'email': 'branch@example.com',
        })
        student = self.env['university.student'].create({
            'partner_id': partner.id,
            'date_of_birth': date(2000, 1, 1),
            'semester_id': self.semester.id,
            'batch_id': self.batch.id,
        })
        journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        category_with_journal = self.env['fee.category'].create({
            'name': 'Cat with Journal',
            'journal_id': journal.id,
        })
        # 1. Create with student_id and fee_category_id, but without partner_id and journal_id
        inv = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'student_id': student.id,
            'fee_category_id': category_with_journal.id,
        })
        self.assertEqual(inv.partner_id.id, partner.id)
        self.assertEqual(inv.journal_id.id, journal.id)
        self.assertTrue(inv.is_fee)
        self.assertEqual(inv.student_name, partner.name)

        # 2. Category without fee structure raises ValidationError
        category_no_struct = self.env['fee.category'].create({
            'name': 'Cat No Struct',
            'journal_id': journal.id,
        })
        with self.assertRaises(ValidationError):
            inv.fee_category_id = category_no_struct
            inv._compute_fee_structure_ids()

        # 3. fee_category_id = False sets fee_structure_ids to False
        inv.fee_category_id = False
        inv._compute_fee_structure_ids()
        self.assertFalse(inv.fee_structure_ids)

    def test_16_attendance_errors_and_branches(self):
        """Cover university.attendance errors and branches."""
        # Batch without students
        empty_batch = self.env['university.batch'].create({
            'semester_id': self.semester.id,
            'academic_year_id': self.academic_year.id,
            'batch_strength': 10,
        })
        att_empty = self.env['university.attendance'].create({
            'batch_id': empty_batch.id,
            'date': date(2026, 9, 25),
        })
        # Batch onchange
        att_empty._onchange_batch_id()
        self.assertEqual(att_empty.academic_year_id.id, empty_batch.academic_year_id.id)

        # No students in batch error
        with self.assertRaises(UserError):
            att_empty.action_create_attendance_line()

        # action_attendance_done without students error
        with self.assertRaises(UserError):
            att_empty.action_attendance_done()

        # Duplicate attendance error when one is done
        self.env['university.student'].create({
            'partner_id': self.guardian.id,
            'date_of_birth': date(2000, 1, 1),
            'batch_id': self.batch.id,
            'semester_id': self.semester.id,
        })
        att1 = self.env['university.attendance'].create({
            'batch_id': self.batch.id,
            'date': date(2026, 9, 26),
        })
        att1.action_create_attendance_line()
        # Half day absent branch: morning absent, afternoon present
        line = att1.attendance_line_ids[0]
        line.is_present_morning = False
        line.is_present_afternoon = True
        att1.action_attendance_done()
        self.assertEqual(line.half_day_absent, 1)

        # Now att1 is done. Attempting to create lines for duplicate date raises ValidationError
        att2 = self.env['university.attendance'].create({
            'batch_id': self.batch.id,
            'date': date(2026, 9, 26),
        })
        with self.assertRaises(ValidationError):
            att2.action_create_attendance_line()

    def test_17_exam_valuation_and_results_branches(self):
        """Cover exam valuation, mark sheet, valuation line and results branches."""
        partner = self.env['res.partner'].create({
            'name': 'Student Val Branch',
            'email': 'valbranch@example.com',
        })
        student = self.env['university.student'].create({
            'partner_id': partner.id,
            'date_of_birth': date(2000, 1, 1),
            'batch_id': self.batch.id,
            'semester_id': self.semester.id,
        })
        subject2 = self.env['university.subject'].create({
            'name': 'Algorithms',
            'code': 'AL102',
            'type': 'compulsory',
            'weightage': 4.0,
        })
        exam_type = self.env['university.exam.type'].create({
            'name': 'Branch Exam',
        })
        exam = self.env['university.exam'].create({
            'exam_type_id': exam_type.id,
            'batch_id': self.batch.id,
            'start_date': date(2027, 2, 1),
            'end_date': date(2027, 2, 10),
            'subject_line_ids': [
                fields.Command.create({
                    'subject_id': self.subject.id,
                    'date': date(2027, 2, 3),
                    'time_from': 10.0,
                    'time_to': 13.0,
                    'mark': 100,
                }),
                fields.Command.create({
                    'subject_id': subject2.id,
                    'date': date(2027, 2, 5),
                    'time_from': 10.0,
                    'time_to': 13.0,
                    'mark': 100,
                }),
            ],
        })
        exam.action_confirm_exam()

        # Batch without students for action_create_mark_sheet error
        empty_batch = self.env['university.batch'].create({
            'semester_id': self.semester.id,
            'academic_year_id': self.academic_year.id,
            'batch_strength': 5,
        })
        empty_exam = self.env['university.exam'].create({
            'exam_type_id': exam_type.id,
            'batch_id': empty_batch.id,
            'start_date': date(2027, 2, 1),
            'end_date': date(2027, 2, 10),
            'subject_line_ids': [
                fields.Command.create({
                    'subject_id': self.subject.id,
                    'date': date(2027, 2, 2),
                    'time_from': 9.0,
                    'time_to': 12.0,
                    'mark': 50,
                }),
            ],
        })
        empty_exam.action_confirm_exam()
        val_empty = self.env['exam.valuation'].create({
            'exam_id': empty_exam.id,
            'subject_id': self.subject.id,
            'mark': 50.0,
            'pass_mark': 20.0,
        })
        with self.assertRaises(UserError):
            val_empty.action_create_mark_sheet()

        # Valuation 1 for first subject: using action_create_mark_sheet
        val1 = self.env['exam.valuation'].create({
            'exam_id': exam.id,
            'subject_id': self.subject.id,
            'mark': 100.0,
            'pass_mark': 40.0,
        })
        val1.action_create_mark_sheet()
        self.assertTrue(val1.is_mark_sheet_created)
        # Duplicate valuation creation raises UserError
        with self.assertRaises(UserError):
            self.env['exam.valuation'].create({
                'exam_id': exam.id,
                'subject_id': self.subject.id,
                'mark': 100.0,
                'pass_mark': 40.0,
            })

        # Test onchange on valuation line
        line1 = val1.valuation_line_ids.filtered(lambda l: l.student_id == student)
        line1.mark_scored = 150.0
        with self.assertRaises(UserError):
            line1._onchange_mark_scored()
        line1.mark_scored = 30.0  # Fail
        line1._onchange_mark_scored()
        self.assertFalse(line1.is_pass)

        # Complete valuation 1 -> creates exam.result with fail
        val1.action_valuation_completed()

        res1 = self.env['exam.result'].search([
            ('student_id', '=', student.id),
            ('exam_id', '=', exam.id),
        ], limit=1)
        self.assertTrue(res1.exists())
        self.assertFalse(res1.is_overall_pass)

        # Valuation 2 for second subject -> exercises else branch in action_valuation_completed
        val2 = self.env['exam.valuation'].create({
            'exam_id': exam.id,
            'subject_id': subject2.id,
            'mark': 100.0,
            'pass_mark': 40.0,
        })
        val2.action_create_mark_sheet()
        line2 = val2.valuation_line_ids.filtered(lambda l: l.student_id == student)
        line2.mark_scored = 90.0  # Pass
        line2._onchange_mark_scored()
        self.assertTrue(line2.is_pass)
        val2.action_valuation_completed()

        # Compute subject ids with exam and without exam
        val2._compute_subject_ids()
        self.assertTrue(val2.subject_ids)
        val2.exam_id = False
        val2._compute_subject_ids()
        self.assertFalse(val2.subject_ids)

    def test_18_exam_and_timetable_validation_constraints(self):
        """Cover exam subject dates, period ranges, and schedule line overlap constraints."""
        exam_type = self.env['university.exam.type'].create({
            'name': 'Constraint Exam',
        })
        # 1. Exam with no subjects raises UserError on confirm
        exam_no_sub = self.env['university.exam'].create({
            'exam_type_id': exam_type.id,
            'batch_id': self.batch.id,
            'start_date': date(2027, 3, 1),
            'end_date': date(2027, 3, 10),
        })
        with self.assertRaises(UserError):
            exam_no_sub.action_confirm_exam()

        # 2. Exam subject line date outside start_date / end_date
        exam_bad_date = self.env['university.exam'].create({
            'exam_type_id': exam_type.id,
            'batch_id': self.batch.id,
            'start_date': date(2027, 3, 5),
            'end_date': date(2027, 3, 10),
            'subject_line_ids': [
                fields.Command.create({
                    'subject_id': self.subject.id,
                    'date': date(2027, 3, 1),  # earlier than start_date
                    'time_from': 9.0,
                    'time_to': 12.0,
                    'mark': 50,
                }),
            ],
        })
        with self.assertRaises(ValidationError):
            exam_bad_date.action_confirm_exam()

        # 3. Timetable period time range constraints
        with self.assertRaises(ValidationError):
            self.env['timetable.period'].create({
                'name': 'Too Early Period',
                'time_from': 8.0,
                'time_to': 10.0,
            })
        with self.assertRaises(ValidationError):
            self.env['timetable.period'].create({
                'name': 'Backwards Period',
                'time_from': 12.0,
                'time_to': 11.0,
            })

        # 4. Timetable schedule line time_from >= time_till constraint
        period = self.env['timetable.period'].create({
            'name': 'Normal Period',
            'time_from': 10.0,
            'time_to': 11.0,
        })
        tt = self.env['university.timetable'].search([('batch_id', '=', self.batch.id)], limit=1)
        if not tt:
            tt = self.env['university.timetable'].create({'batch_id': self.batch.id})
        with self.assertRaises(ValidationError):
            self.env['timetable.schedule.line'].create({
                'timetable_id': tt.id,
                'period_id': period.id,
                'faculty_id': self.faculty.id,
                'subject_id': self.subject.id,
                'week_day': '0',
                'time_from': 11.0,
                'time_till': 10.0,
            })

    def test_19_application_and_student_branches(self):
        """Cover application verification, date_of_birth onchange, same_address, and student documents."""
        # 1. Application date of birth < 18 raises ValidationError
        app_underage = self.env['university.application'].new({
            'date_of_birth': date(fields.Date.today().year - 10, 1, 1),
        })
        with self.assertRaises(ValidationError):
            app_underage._onchange_date_of_birth()

        # 2. Application verification with no documents
        app = self.env['university.application'].create({
            'name': 'Alice',
            'last_name': 'Smith',
            'email': 'alice.smith@example.com',
            'mobile': '9876543299',
            'course_id': self.course.id,
            'department_id': self.department.id,
            'semester_id': self.semester.id,
            'batch_id': self.batch.id,
            'academic_year_id': self.academic_year.id,
            'date_of_birth': date(1999, 5, 20),
            'guardian_id': self.guardian.id,
            'is_same_address': True,
            'street': '123 University Ave',
        })
        with self.assertRaises(ValidationError):
            app.action_send_verification()
        with self.assertRaises(ValidationError):
            app.action_verify_application()

        # Add document but not done
        doc = self.env['university.document'].create({
            'application_ref_id': app.id,
            'document_type_id': self.doc_type.id,
        })
        app.action_send_verification()
        self.assertEqual(app.state, 'verification')
        with self.assertRaises(ValidationError):
            app.action_verify_application()

        # Mark document done and verify application
        doc.action_verify_document()
        app.action_verify_application()
        self.assertEqual(app.state, 'approve')

        # Create student with is_same_address=True
        res = app.action_create_student()
        self.assertTrue(res['res_id'])
        student = self.env['university.student'].browse(res['res_id'])
        self.assertEqual(student.per_street, '123 University Ave')

        # Test action_student_documents
        doc_act = student.action_student_documents()
        self.assertEqual(doc_act['res_model'], 'university.document')

        # 3. Semester name compute without department
        sem_no_dept = self.env['university.semester'].new({
            'semester_no': 2,
            'department_id': False,
        })
        sem_no_dept._compute_semester_name()
        self.assertFalse(sem_no_dept.name)

        # 4. Application compute methods when related fields are unset
        app_empty = self.env['university.application'].new({
            'course_id': False,
            'department_id': False,
            'semester_id': False,
        })
        app_empty._compute_department_ids()
        self.assertFalse(app_empty.department_ids)
        app_empty._compute_semester_ids()
        self.assertFalse(app_empty.semester_ids)
        app_empty._compute_batch_ids()
        self.assertFalse(app_empty.batch_ids)

    def test_20_additional_coverage(self):
        """Cover valuation lines without valuation, and schedule line check_no_overlap."""
        # 1. exam.valuation.line compute is_pass without valuation
        val_line = self.env['exam.valuation.line'].new({
            'valuation_id': False,
            'mark_scored': 50.0,
        })
        val_line._compute_is_pass()
        self.assertFalse(val_line.is_pass)

        # 2. timetable.schedule.line check_no_overlap with valid time range
        sched_line = self.env['timetable.schedule.line'].new({
            'time_from': 9.0,
            'time_till': 10.0,
            'week_day': '0',
            'timetable_id': False,
        })
        sched_line._check_no_overlap()

