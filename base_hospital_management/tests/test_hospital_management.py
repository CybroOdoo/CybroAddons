# -*- coding: utf-8 -*-
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
from datetime import date, timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHospitalManagement(TransactionCase):
    """Test suite covering hospital management workflows."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Doctor Job & Employee
        cls.doctor_job = cls.env['hr.job'].create({
            'name': 'Doctor',
        })
        cls.doctor_employee = cls.env['hr.employee'].create({
            'name': 'Dr. Robert Smith',
            'job_id': cls.doctor_job.id,
            'doctor': True,
            'time_avg': 15.0,
        })

        # Patients
        cls.patient_john = cls.env['res.partner'].create({
            'name': 'John Patient',
            'date_of_birth': date(1985, 5, 20),
            'blood_group': 'o',
            'rh_type': '+',
            'gender': 'male',
            'marital_status': 'married',
            'phone': '1234567890',
        })

        cls.patient_jane = cls.env['res.partner'].create({
            'name': 'Jane Patient',
            'date_of_birth': date(1992, 8, 15),
            'blood_group': 'a',
            'rh_type': '+',
            'gender': 'female',
            'phone': '9876543210',
        })

        # Infrastructure: Building, Ward, Room, Bed
        cls.building = cls.env['hospital.building'].create({
            'name': 'Main Clinical Block',
        })
        cls.ward = cls.env['hospital.ward'].create({
            'ward_no': 'Ward-A-101',
            'building_id': cls.building.id,
            'floor_no': 1,
        })
        cls.room = cls.env['patient.room'].create({
            'name': 'Room 101',
            'building_id': cls.building.id,
            'rent': 500.0,
            'bed_type': 'electric',
        })
        cls.bed = cls.env['hospital.bed'].create({
            'name': 'Bed-101-A',
            'ward_id': cls.ward.id,
            'room_id': cls.room.id,
            'bed_rent': 200.0,
            'bed_type': 'electric',
        })

        # Products: Medicine and Vaccine
        cls.medicine_product = cls.env['product.template'].create({
            'name': 'Paracetamol 500mg',
            'medicine_ok': True,
            'list_price': 15.0,
        })
        cls.vaccine_product = cls.env['product.template'].create({
            'name': 'Hepatitis B Vaccine',
            'vaccine_ok': True,
            'list_price': 75.0,
        })

        # Lab Test
        cls.lab_test = cls.env['lab.test'].create({
            'name': 'Complete Blood Count',
            'price': 40.0,
            'patient_lead': 2.0,
            'test_type': 'range',
        })

        # Doctor Allocation
        cls.allocation = cls.env['doctor.allocation'].create({
            'doctor_id': cls.doctor_employee.id,
            'date': fields.Date.today(),
            'work_from': 9.0,
            'work_to': 17.0,
            'state': 'confirm',
        })

    def test_01_patient_management(self):
        """Test patient creation, sequence generation, barcode, and helper actions."""
        # Check patient sequence generated
        self.assertTrue(self.patient_john.patient_seq)
        self.assertNotEqual(self.patient_john.patient_seq, 'New')

        # Test action_alive_status toggle
        self.assertEqual(self.patient_john.is_alive, 'alive')
        self.patient_john.action_alive_status()
        self.assertEqual(self.patient_john.is_alive, 'dead')
        self.patient_john.action_alive_status()
        self.assertEqual(self.patient_john.is_alive, 'alive')

        # Test generate_ean & ean_checksum
        checksum = self.patient_john.ean_checksum('123456789012')
        self.assertIsInstance(checksum, int)
        ean = self.patient_john.generate_ean(str(self.patient_john.id))
        self.assertEqual(len(ean), 13)

        # Test action_generate_patient_card (tests in-memory barcode generation)
        res = self.patient_john.action_generate_patient_card()
        self.assertTrue(res)
        self.assertTrue(self.patient_john.barcode)
        self.assertTrue(self.patient_john.barcode_png)

        # Test patient card generation for gender 'other'
        patient_other = self.env['res.partner'].create({
            'name': 'Other Gender Patient',
            'gender': 'other',
            'date_of_birth': fields.Date.today(),
        })
        card_res = patient_other.action_generate_patient_card()
        self.assertTrue(card_res)

        # Test reception_op_barcode
        patient_data = self.env['res.partner'].reception_op_barcode({'patient_data': self.patient_john.id})
        self.assertEqual(patient_data.get('name'), self.patient_john.name)

        # Test action_view_invoice and compute
        inv_action = self.patient_john.action_view_invoice()
        self.assertEqual(inv_action.get('res_model'), 'account.move')
        self.patient_john._compute_invoice_count()
        self.assertEqual(self.patient_john.invoice_count, 0)

    def test_02_doctor_allocation_and_slots(self):
        """Test doctor allocation limits, slot calculation, and doctor slots."""
        # (17.0 - 9.0) = 8.0 hours * 60 = 480 minutes / 15.0 = 32 slots
        self.allocation._compute_patient_limit()
        self.assertEqual(self.allocation.patient_limit, 32)
        self.allocation._compute_slot_remaining()
        self.assertEqual(self.allocation.slot_remaining, 32)

        # Test validation error when work_from >= work_to
        invalid_alloc = self.env['doctor.allocation'].new({
            'doctor_id': self.doctor_employee.id,
            'work_from': 18.0,
            'work_to': 9.0,
        })
        with self.assertRaises(ValidationError):
            invalid_alloc._onchange_work_from()

        # Doctor slot workflow
        slot = self.env['doctor.slot'].create({
            'name': 'Appendectomy Consultation',
            'doctor_id': self.doctor_employee.id,
            'patient_id': self.patient_john.id,
            'date_start': fields.Datetime.now(),
            'state': 'confirmed',
        })
        confirmed_slots = slot.hospital_inpatient_confirm()
        self.assertIsInstance(confirmed_slots, list)
        slot.state = 'cancel'
        cancelled_slots = slot.hospital_inpatient_cancel()
        self.assertIsInstance(cancelled_slots, list)
        slot.state = 'done'
        done_slots = slot.hospital_inpatient_done()
        self.assertIsInstance(done_slots, list)

    def test_03_hospital_infrastructure(self):
        """Test buildings, wards, rooms, facilities, and beds."""
        facility = self.env['room.facility'].create({
            'name': 'Oxygen Concentrator',
        })
        self.room.room_facilities_ids = [(4, facility.id)]
        self.assertIn(facility, self.room.room_facilities_ids)

        # Test bed initial state
        self.assertEqual(self.bed.state, 'avail')
        self.bed.state = 'not'
        self.assertEqual(self.bed.state, 'not')
        self.bed.state = 'avail'

        # Test ward bed_count compute and open beds action domain
        self.ward._compute_bed_count()
        self.assertEqual(self.ward.bed_count, 1)
        bed_act = self.ward.action_get_open_bed()
        self.assertEqual(bed_act.get('domain'), [('ward_id', '=', self.ward.id)])

    def test_04_outpatient_workflow(self):
        """Test outpatient consultation creation, actions, duplicate check, and prescription lines."""
        outpatient = self.env['hospital.outpatient'].create({
            'patient_id': self.patient_john.id,
            'doctor_id': self.allocation.id,
            'op_date': fields.Date.today(),
            'reason': 'Fever and Cough',
        })
        self.assertTrue(outpatient.op_reference)

        # Duplicate OP check
        with self.assertRaises(ValidationError):
            self.env['hospital.outpatient'].create({
                'patient_id': self.patient_john.id,
                'doctor_id': self.allocation.id,
                'op_date': fields.Date.today(),
            })

        # Add prescription line
        presc_line = self.env['prescription.line'].create({
            'outpatient_id': outpatient.id,
            'medicine_id': self.medicine_product.id,
            'quantity': 10,
            'no_intakes': 1.0,
            'time': 'twice',
            'note': 'after',
        })
        self.assertIn(presc_line, outpatient.prescription_ids)

        # Confirm OP and verify slot allocation
        outpatient.action_confirm()
        self.assertEqual(outpatient.state, 'op')
        self.assertGreater(outpatient.slot, 0)

        # Test row click data helper
        row_data = self.env['hospital.outpatient'].action_row_click_data(outpatient.op_reference)
        self.assertTrue(row_data.get('op_data'))
        self.assertTrue(row_data.get('medicines'))

        # Test onchange op_date
        outpatient._onchange_op_date()

        # Test lab test action from outpatient
        lab_action = outpatient.action_create_lab_test()
        self.assertEqual(lab_action.get('res_model'), 'lab.test.line')
        self.assertEqual(lab_action.get('context', {}).get('default_patient_id'), self.patient_john.id)

        view_test_action = outpatient.action_view_test()
        self.assertEqual(view_test_action.get('res_model'), 'lab.test.line')

        # Convert to inpatient action
        conv_action = outpatient.action_convert_to_inpatient()
        self.assertEqual(conv_action.get('res_model'), 'hospital.inpatient')
        self.assertEqual(outpatient.state, 'inpatient')

        # Cancel action
        outpatient.action_op_cancel()
        self.assertEqual(outpatient.state, 'cancel')

    def test_05_inpatient_workflow(self):
        """Test inpatient admission, rent calculation, states, and surgery."""
        today = fields.Date.today()
        inpatient = self.env['hospital.inpatient'].create({
            'patient_id': self.patient_john.id,
            'attending_doctor_id': self.doctor_employee.id,
            'type_admission': 'routine',
            'room_id': self.room.id,
            'bed_id': self.bed.id,
            'hosp_date': today - timedelta(days=3),
            'discharge_date': today,
            'reason': 'Pneumonia observation',
        })
        # Compute rent amounts
        inpatient._compute_room_rent_amount()
        inpatient._compute_bed_rent_amount()
        # 4 days (3 days ago to today inclusive): Room rent 500 * 4 = 2000, Bed rent 200 * 4 = 800
        self.assertEqual(inpatient.admit_days, 4)
        self.assertEqual(inpatient.room_rent_amount, 2000.0)
        self.assertEqual(inpatient.bed_rent_amount, 800.0)

        # State transitions: Reserve -> Admit -> Discharge
        inpatient.action_reserve()
        self.assertEqual(inpatient.state, 'reserve')
        inpatient.action_admit()
        self.assertEqual(inpatient.state, 'admit')

        # Inpatient actions
        lab_action = inpatient.action_create_lab_test()
        self.assertEqual(lab_action.get('res_model'), 'lab.test.line')
        view_tests = inpatient.action_view_tests()
        self.assertEqual(view_tests.get('res_model'), 'patient.lab.test')
        view_test = inpatient.action_view_test()
        self.assertEqual(view_test.get('res_model'), 'lab.test.line')

        # Discharge
        inpatient.action_discharge()
        self.assertEqual(inpatient.state, 'dis')

        # Inpatient list and fetch helpers
        inpatient_list = self.env['hospital.inpatient'].hospital_inpatient_list()
        self.assertIsInstance(inpatient_list, list)
        fetched = self.env['hospital.inpatient'].fetch_inpatient({'patient_id': self.patient_john.id})
        self.assertIsInstance(fetched, list)

        # Test invoice view action
        inv_action = inpatient.action_view_invoice()
        self.assertEqual(inv_action.get('res_model'), 'account.move')

        # Create inpatient surgery
        surgery = self.env['inpatient.surgery'].create({
            'name': 'Appendectomy',
            'inpatient_id': inpatient.id,
            'doctor_id': self.doctor_employee.id,
            'planned_date': fields.Datetime.now(),
            'hours_to_take': 2.0,
        })
        self.assertTrue(surgery)
        surgery.action_confirm()
        self.assertEqual(surgery.state, 'confirmed')
        surgery.action_done()
        self.assertEqual(surgery.state, 'done')
        surgery.action_cancel()
        self.assertEqual(surgery.state, 'cancel')

    def test_06_laboratory_workflow(self):
        """Test laboratory, lab test ordering, confirmation, and result logging."""
        lab = self.env['hospital.laboratory'].create({
            'phone': '1122334455',
            'email': 'lab@hospital.com',
        })
        self.assertTrue(lab)

        # Create lab test line for outpatient
        lab_line = self.env['lab.test.line'].create({
            'patient_id': self.patient_john.id,
            'doctor_id': self.doctor_employee.id,
            'patient_type': 'outpatient',
            'test_ids': [(4, self.lab_test.id)],
        })
        self.assertEqual(lab_line.state, 'draft')

        # Confirm test line (creates patient.lab.test)
        lab_line.action_confirm()
        self.assertEqual(lab_line.state, 'created')

        patient_test = self.env['patient.lab.test'].search([
            ('test_id', '=', lab_line.id),
        ], limit=1)
        self.assertTrue(patient_test)
        self.assertEqual(patient_test.total_price, 40.0)

        # Start test (creates result_ids)
        self.env['patient.lab.test'].start_test(patient_test.id)
        self.assertEqual(patient_test.state, 'test')
        self.assertTrue(patient_test.result_ids)

        # Test patient_lab_test button actions & computes
        patient_test.action_start_test()
        patient_test.action_test_end()
        self.assertEqual(patient_test.state, 'completed')
        inv_action = patient_test.action_view_invoice()
        self.assertEqual(inv_action.get('res_model'), 'account.move')
        so_action = patient_test.action_view_sale_order()
        self.assertEqual(so_action.get('res_model'), 'sale.order')
        patient_test._compute_invoice_count()
        patient_test._compute_sale_count()
        patient_test._compute_medicine_ids()

        # Test print results
        results = self.env['lab.test.result'].print_test_results()
        self.assertIsInstance(results, list)
        if results:
            self.assertIn('access_token', results[0])

    def test_07_pharmacy_and_medicines(self):
        """Test pharmacy, medicine stock, and product helper methods."""
        brand = self.env['medicine.brand'].create({
            'name': 'PharmaCorp',
        })
        self.assertTrue(brand.id)
        pharmacy = self.env['hospital.pharmacy'].create({
            'name': 'Central Hospital Pharmacy',
        })
        med_entry = self.env['pharmacy.medicine'].create({
            'pharmacy_id': pharmacy.id,
            'product_id': self.medicine_product.id,
        })
        self.assertIn(med_entry, pharmacy.medicine_ids)

        # Test pharmacy actions and helpers
        curr = pharmacy.company_currency()
        self.assertTrue(curr)
        inv_action = pharmacy.action_get_inventory()
        self.assertEqual(inv_action.get('res_model'), 'stock.quant')
        so_action = pharmacy.action_get_sale_order()
        self.assertEqual(so_action.get('res_model'), 'sale.order')
        so_data = pharmacy.fetch_sale_orders()
        self.assertIsInstance(so_data, list)

        # Test product template helper methods
        med_data = self.env['product.template'].action_get_medicine_data()
        self.assertIsInstance(med_data, list)
        vacc_data = self.env['product.template'].action_get_vaccine_data()
        self.assertIsInstance(vacc_data, list)

    def test_08_blood_bank_workflow(self):
        """Test blood bank donation, contraindications, and availability toggle."""
        contra = self.env['contra.indication'].create({
            'blood_donation_question': 'Have you traveled abroad in the last 30 days?',
        })
        self.assertTrue(contra.id)
        blood_entry = self.env['blood.bank'].create({
            'partner_id': self.patient_john.id,
            'blood_type': 'o_positive',
            'date': fields.Date.today(),
        })
        # Test onchange to populate questions
        blood_entry._onchange_partner_id()
        self.assertTrue(blood_entry.blood_donation_ids)

        # Toggle state to unavailable
        self.assertEqual(blood_entry.state, 'avail')
        blood_entry.action_blood_available()
        self.assertEqual(blood_entry.state, 'not')

        # Test cron state change
        blood_entry.date = fields.Date.subtract(fields.Date.today(), months=2)
        blood_entry.action_change_availability()
        self.assertEqual(blood_entry.state, 'avail')

        # Test expand states helper
        states = blood_entry._group_expand_states([], [])
        self.assertIn('o_positive', states)

    def test_09_vaccination_workflow(self):
        """Test vaccination records and data fetching."""
        vacc = self.env['hospital.vaccination'].create({
            'patient_id': self.patient_john.id,
            'vaccine_product_id': self.vaccine_product.id,
            'vaccine_date': fields.Date.today(),
            'dose': 1.0,
        })
        self.assertTrue(vacc.name)
        self.assertNotEqual(vacc.name, 'New')

        # Test onchange next vaccine days
        vacc.next_vaccine_days = 30
        vacc._onchange_next_vaccine_days()
        self.assertEqual(vacc.next_vaccine, fields.Date.today() + timedelta(days=30))

        # Test action_create_so and action_get_sale_order
        vacc.action_create_so()
        self.assertTrue(vacc.sale_order_id)
        so_action = vacc.action_get_sale_order()
        self.assertEqual(so_action.get('res_model'), 'sale.order')

        # Test fetch vaccination data
        data = self.env['hospital.vaccination'].fetch_vaccination_data(domain=[('id', '=', vacc.id)])
        self.assertTrue(data)
        self.assertEqual(data[0]['patient_id'][0], self.patient_john.id)

    def test_10_edge_cases_and_multi_recordset(self):
        """Test multi-recordset actions, computes, and edge cases."""
        patients = self.patient_john | self.patient_jane
        patients._compute_invoice_count()
        schedule_act = self.patient_john.action_schedule()
        self.assertEqual(schedule_act.get('res_model'), 'hospital.outpatient')
        phone_data = self.env['res.partner'].reception_op_phone({'patient-phone': self.patient_john.phone})
        self.assertEqual(phone_data.get('name'), self.patient_john.name)
        p_data = self.patient_john.fetch_patient_data()
        self.assertIsInstance(p_data, list)

        # Multi-recordset for hospital beds
        beds = self.bed | self.env['hospital.bed'].create({
            'name': 'Bed-Multi-02',
            'ward_id': self.ward.id,
            'bed_rent': 250.0,
        })
        self.assertEqual(len(beds), 2)

        # Test patient display name / search
        self.assertTrue(self.patient_john.display_name)
        search_res = self.env['res.partner'].name_search('John Patient')
        self.assertTrue(search_res)

    def test_11_pharmacy_and_sale_orders(self):
        """Test pharmacy create_sale_order with multiple parameter combinations."""
        pharmacy = self.env['hospital.pharmacy'].search([], limit=1)
        if not pharmacy:
            pharmacy = self.env['hospital.pharmacy'].create({'name': 'Test Pharmacy'})

        # 1. With patient_id
        res1 = pharmacy.create_sale_order({
            'patient_id': self.patient_john.id,
            'products': [{'product': self.medicine_product.id, 'qty': 2, 'price': 25.0}],
        })
        self.assertTrue(res1.get('invoice_id'))

        # 2. With patient_code
        res2 = pharmacy.create_sale_order({
            'patient_code': self.patient_john.patient_seq,
            'products': [{'product': self.medicine_product.id, 'qty': 1, 'price': 20.0}],
        })
        self.assertTrue(res2.get('invoice_id'))

        # 3. With op reference
        op = self.env['hospital.outpatient'].create({
            'patient_id': self.patient_john.id,
            'doctor_id': self.allocation.id,
            'op_date': fields.Date.today(),
            'reason': 'Pharmacy test checkup',
        })
        res3 = pharmacy.create_sale_order({
            'op': op.op_reference,
            'products': [{'product': self.medicine_product.id, 'qty': 1, 'price': 15.0}],
        })
        self.assertTrue(res3.get('invoice_id'))

        # 4. With new patient info
        res4 = pharmacy.create_sale_order({
            'name': 'Walk-in Pharmacy Patient',
            'email': 'walkin@example.com',
            'phone': '5551234567',
            'dob': '1990-01-01',
            'gender': 'female',
            'products': [{'product': self.medicine_product.id, 'qty': 3}],
        })
        self.assertTrue(res4.get('invoice_id'))

        # Test pharmacy helper methods
        self.assertTrue(pharmacy.company_currency())
        inv_act = pharmacy.action_get_inventory()
        self.assertEqual(inv_act.get('res_model'), 'stock.quant')
        so_act = pharmacy.action_get_sale_order()
        self.assertEqual(so_act.get('res_model'), 'sale.order')
        so_list = pharmacy.fetch_sale_orders()
        self.assertIsInstance(so_list, list)
        tax = self.env['account.tax'].search([], limit=1)
        if tax:
            t_res = pharmacy.tax_amount(tax.id)
            self.assertIn('amount', t_res)

    def test_12_patient_lab_test_and_results_helpers(self):
        """Test patient lab test helpers, status changes, and report rendering."""
        lab_line = self.env['lab.test.line'].create({
            'patient_id': self.patient_john.id,
            'doctor_id': self.doctor_employee.id,
            'patient_type': 'outpatient',
            'test_ids': [(6, 0, [self.lab_test.id])],
        })
        lab_line.action_confirm()

        patient_test = self.env['patient.lab.test'].search([('test_id', '=', lab_line.id)], limit=1)
        self.assertTrue(patient_test)

        # Test action_get_patient_data
        data = self.env['patient.lab.test'].action_get_patient_data(patient_test.id)
        self.assertTrue(data)
        self.assertEqual(data.get('name'), self.patient_john.name)

        # Test lab.test.line helpers
        line_data = self.env['lab.test.line'].action_get_patient_data(lab_line.id)
        self.assertTrue(line_data)

        # Test test_end and create_invoice
        self.env['patient.lab.test'].test_end(patient_test.id)
        self.assertEqual(patient_test.state, 'completed')

        patient_test.action_create_invoice()
        self.assertTrue(patient_test.invoiced)

        # Smart buttons
        inv_view = patient_test.action_view_invoice()
        self.assertEqual(inv_view.get('res_model'), 'account.move')

        report = patient_test.print_lab_tests()
        self.assertTrue(report)

        # Test printing lab test as a non-HR lab assistant user (ensuring no hr.employee.public access error)
        lab_user = self.env['res.users'].create({
            'name': 'Lab Tech User',
            'login': 'lab_tech_test_user',
            'email': 'labtech@hospital.test',
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('base_hospital_management.base_hospital_management_group_lab_assistant').id,
            ])],
        })
        report_lab_user = patient_test.with_user(lab_user).print_lab_tests()
        self.assertTrue(report_lab_user)

    def test_13_inpatient_and_outpatient_additional_workflows(self):
        """Test additional inpatient and outpatient actions and reports."""
        inpatient = self.env['hospital.inpatient'].create({
            'patient_id': self.patient_john.id,
            'type_admission': 'routine',
            'attending_doctor_id': self.doctor_employee.id,
            'hosp_date': fields.Date.today(),
            'is_ward': 'ward',
            'ward_id': self.ward.id,
            'bed_id': self.bed.id,
        })
        inpatient.action_reserve()

        # Inpatient test_count compute
        self.assertEqual(inpatient.test_count, 0)
        self.env['patient.lab.test'].create({
            'patient_id': self.patient_john.id,
            'inpatient_id': inpatient.id,
            'date': fields.Date.today(),
        })
        inpatient._compute_test_count()
        self.assertEqual(inpatient.test_count, 1)

        # Add prescription to inpatient and print
        self.env['prescription.line'].create({
            'inpatient_id': inpatient.id,
            'medicine_id': self.medicine_product.id,
            'quantity': 5,
            'time': 'twice',
            'no_intakes': 2,
            'note': 'after',
        })
        presc_report = inpatient.action_print_prescription()
        self.assertTrue(presc_report)

        # Inpatient dashboard list and fetch
        ip_list = self.env['hospital.inpatient'].hospital_inpatient_list()
        self.assertIsInstance(ip_list, list)
        fetch_data = self.env['hospital.inpatient'].fetch_inpatient(False)
        self.assertIsInstance(fetch_data, list)
        fetch_data2 = self.env['hospital.inpatient'].fetch_inpatient('routine')
        self.assertIsInstance(fetch_data2, list)

        # Inpatient invoice action
        inv_res = inpatient.action_invoice()
        self.assertTrue(inpatient.invoice_id)
        self.assertEqual(inv_res.get('res_model'), 'account.move')

        # Inpatient admit and discharge
        inpatient.action_admit()
        self.assertEqual(inpatient.state, 'admit')
        inpatient.action_discharge()
        self.assertEqual(inpatient.state, 'dis')

        # Outpatient extra actions
        outpatient = self.env['hospital.outpatient'].create({
            'patient_id': self.patient_jane.id,
            'doctor_id': self.allocation.id,
            'op_date': fields.Date.today(),
            'reason': 'Fever and cold',
        })
        outpatient.action_confirm()
        outpatient.create_invoice()
        self.assertTrue(outpatient.invoice_id)
        view_inv = outpatient.action_view_invoice()
        self.assertEqual(view_inv.get('res_model'), 'account.move')

        # Outpatient prescription file generation
        self.env['prescription.line'].create({
            'outpatient_id': outpatient.id,
            'medicine_id': self.medicine_product.id,
            'quantity': 2,
            'time': 'morning',
            'no_intakes': 1,
            'note': 'before',
        })
        file_res = outpatient._create_prescription_file()
        self.assertTrue(file_res)
        self.assertIn('url', file_res)
        self.assertTrue(outpatient.attachment_id)

    def test_14_doctor_allocation_slots_and_infrastructure(self):
        """Test doctor allocations, slots, building, and ward helpers."""
        # Allocation helpers
        booking_act = self.allocation.action_get_patient_booking()
        self.assertEqual(booking_act.get('res_model'), 'hospital.outpatient')
        lines = self.env['doctor.allocation'].get_allocation_lines()
        self.assertIsInstance(lines, list)

        # Cancel allocation
        self.allocation.action_cancel_allocation()
        self.assertEqual(self.allocation.state, 'cancel')

        # Slot helpers
        slot = self.env['doctor.slot'].create({
            'name': 'Slot-Test-01',
            'doctor_id': self.doctor_employee.id,
            'date_start': fields.Datetime.now(),
            'patient_id': self.patient_john.id,
            'state': 'draft',
        })
        slot.action_confirm()
        self.assertEqual(slot.state, 'confirmed')
        self.env['doctor.slot'].hospital_inpatient_confirm()
        slot.action_done()
        self.assertEqual(slot.state, 'done')
        self.env['doctor.slot'].hospital_inpatient_done()
        slot.action_cancel()
        self.assertEqual(slot.state, 'cancel')
        self.env['doctor.slot'].hospital_inpatient_cancel()
        slot_data = self.env['doctor.slot'].action_get_doctor_slot()
        self.assertIsInstance(slot_data, list)

        # Building & Ward helpers
        self.assertTrue(self.building.name)
        room_act = self.building.action_get_room_count()
        self.assertEqual(room_act.get('res_model'), 'patient.room')
        ward_act = self.building.action_get_ward_count()
        self.assertEqual(ward_act.get('res_model'), 'hospital.ward')

        bed_act = self.ward.action_get_open_bed()
        self.assertEqual(bed_act.get('res_model'), 'hospital.bed')
        wards = self.env['hospital.ward'].fetch_ward_details()
        self.assertIsInstance(wards, list)
        rooms = self.env['patient.room'].fetch_rooms_details()
        self.assertIsInstance(rooms, list)

    def test_15_res_partner_users_and_payments(self):
        """Test partner data retrieval, user creation, employee helpers, and payment register."""
        # Partner action_get_patient_data
        p_data = self.patient_john.action_get_patient_data(self.patient_john.name)
        self.assertEqual(p_data.get('name'), self.patient_john.name)
        p_empty = self.patient_john.action_get_patient_data(False)
        self.assertEqual(p_empty.get('name'), 'Patient Not Found')

        # Reception barcode and phone helpers
        bc_res = self.env['res.partner'].reception_op_barcode({'patient_data': self.patient_john.id})
        self.assertEqual(bc_res.get('name'), self.patient_john.name)
        phone_res = self.env['res.partner'].reception_op_phone({'patient-phone': self.patient_john.phone})
        self.assertEqual(phone_res.get('name'), self.patient_john.name)

        # Partner fetch_patient_data
        p_list = self.env['res.partner'].fetch_patient_data()
        self.assertIsInstance(p_list, list)

        # Partner create_patient helper
        self.env['res.partner'].create_patient({
            'patient_id': False,
            'op_name': 'Emergency Walk-in Patient',
            'op_blood_group': 'b',
            'op_gender': 'male',
            'date': str(fields.Date.today()),
            'reason': 'Acute pain',
        })

        # Res.users creation override
        test_user = self.env['res.users'].create({
            'name': 'Hospital Portal User',
            'login': 'hospital_portal_user@example.com',
        })
        self.assertEqual(test_user.partner_id.patient_seq, 'User')

        # Employee user creation and doctor fetch
        user_act = self.doctor_employee.action_create_user()
        self.assertEqual(user_act.get('res_model'), 'res.users')
        self.doctor_employee._inverse_work_contact_details()
        doctors = self.env['hr.employee'].fetch_doctors_for_reception([('doctor', '=', True)])
        self.assertIsInstance(doctors, list)

        # Inpatient payment via account.payment.register
        inpatient = self.env['hospital.inpatient'].create({
            'patient_id': self.patient_john.id,
            'type_admission': 'emergency',
            'attending_doctor_id': self.doctor_employee.id,
            'hosp_date': fields.Date.today(),
        })
        income_account = self.env['account.account'].search([('account_type', '=', 'income')], limit=1)
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.patient_john.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {'name': 'Hospital Service', 'price_unit': 200.0, 'account_id': income_account.id})],
        })
        invoice.action_post()
        self.env['account.payment.register'].with_context(
            active_model='account.move',
            active_ids=invoice.ids,
        ).create({
            'communication': 'Deposit payment',
            'amount': 200.0,
            'payment_date': fields.Date.today(),
        })
        payments = self.env['inpatient.payment'].search([('inpatient_id', '=', inpatient.id)])
        self.assertTrue(payments)
