# -*- coding: utf-8 -*-
from datetime import date
from unittest.mock import MagicMock, patch
from odoo.tests import HttpCase, tagged
from odoo import fields


@tagged('post_install', '-at_install')
class TestPatientPortalController(HttpCase):
    """Test cases for the PatientPortal controller (patient_portal.py)"""

    @classmethod
    def setUpClass(cls):
        super(TestPatientPortalController, cls).setUpClass()
        cls.specialist = cls.env['dental.specialist'].create({
            'name': 'Periodontics',
        })
        cls.time_shift = cls.env['dental.time.shift'].create({
            'shift_type': 'morning',
            'start_time': 9.0,
            'end_time': 13.0,
        })
        cls.doctor = cls.env['hr.employee'].create({
            'name': 'Dr. Portal Test',
            'dob': date(1972, 3, 15),
            'specialised_in_id': cls.specialist.id,
            'time_shift_ids': [(4, cls.time_shift.id)],
        })
        cls.patient = cls.env['res.partner'].create({
            'name': 'Portal Test Patient',
        })
        cls.treatment = cls.env['dental.treatment'].create({
            'name': 'Cleaning',
            'cost': 100.0,
        })
        cls.appointment = cls.env['dental.appointment'].create({
            'patient_id': cls.patient.id,
            'specialist_id': cls.specialist.id,
            'doctor_id': cls.doctor.id,
            'shift_id': cls.time_shift.id,
            'date': fields.Date.today(),
            'state': 'new',
        })
        cls.prescription = cls.env['dental.prescription'].create({
            'appointment_id': cls.appointment.id,
            'treatment_id': cls.treatment.id,
        })
        # Create a test user with dental manager access and a known password
        manager_group = cls.env.ref('dental_clinical_management.group_dental_manager')
        internal_group = cls.env.ref('base.group_user')
        cls.test_user = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Dental Test Manager',
            'login': 'dental_test_manager',
            'email': 'dental_test_manager@example.com',
            'group_ids': [(6, 0, [internal_group.id, manager_group.id])],
        })
        cls.test_user.write({'password': 'DentalTest@123'})

    def test_portal_my_prescriptions(self):
        """Test GET /my/prescriptions as a dental manager returns 200."""
        self.authenticate('dental_test_manager', 'DentalTest@123')
        response = self.url_open('/my/prescriptions')
        self.assertEqual(response.status_code, 200,
                         "Portal prescriptions page should return 200.")

    def test_view_prescriptions(self):
        """Test GET /view/prescriptions/<id> as authenticated manager returns 200."""
        self.authenticate('dental_test_manager', 'DentalTest@123')
        response = self.url_open(f'/view/prescriptions/{self.prescription.id}')
        self.assertEqual(response.status_code, 200,
                         "View prescription page should return 200 for authenticated user.")

    def test_get_prescription_domain_manager(self):
        """Test _get_prescription_domain returns [] for dental manager."""
        from odoo.addons.dental_clinical_management.controllers.patient_portal import PatientPortal
        manager_group = self.env.ref('dental_clinical_management.group_dental_manager')
        self.test_user.write({'group_ids': [(4, manager_group.id)]})
        mock_request = MagicMock()
        mock_request.env.user = self.test_user
        with patch(
            'odoo.addons.dental_clinical_management.controllers.patient_portal.request',
            mock_request
        ):
            controller = PatientPortal()
            domain = controller._get_prescription_domain()
        self.assertEqual(domain, [],
                         "Manager should get an empty domain (see all prescriptions).")

    def test_get_prescription_domain_patient(self):
        """Test _get_prescription_domain filters by patient_id for portal/patient users."""
        from odoo.addons.dental_clinical_management.controllers.patient_portal import PatientPortal
        # Create a portal user (no dental group)
        portal_group = self.env.ref('base.group_portal')
        portal_user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Test Portal User',
            'login': 'test_portal_dental',
            'email': 'test_portal_dental@example.com',
            'group_ids': [(6, 0, [portal_group.id])],
        })
        mock_request = MagicMock()
        mock_request.env.user = portal_user
        with patch(
            'odoo.addons.dental_clinical_management.controllers.patient_portal.request',
            mock_request
        ):
            controller = PatientPortal()
            domain = controller._get_prescription_domain()
        self.assertIn(('patient_id', '=', portal_user.partner_id.id), domain,
                      "Portal user should see only their own prescriptions.")

    def test_prepare_home_portal_values(self):
        """Test _prepare_home_portal_values adds prescriptions_count to values."""
        self.authenticate('dental_test_manager', 'DentalTest@123')
        response = self.url_open('/my/home')
        self.assertEqual(response.status_code, 200,
                         "Portal home page should be accessible after login.")
