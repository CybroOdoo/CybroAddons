# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestServiceBooking(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Customer
        cls.partner = cls.env['res.partner'].create({
            'name': 'John',
            'phone': '9876543210'
        })

        # Vehicle brand
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'BMW'
        })

        # Vehicle model
        cls.vehicle_model = cls.env['fleet.vehicle.model'].create({
            'name': 'BMW X5',
            'vehicle_type': 'car',
            'brand_id': cls.brand.id,
        })

        cls.service_type = cls.env['service.type'].create({
            'name': 'Oil Change',
            'amount': 0.0
        })

        cls.package_line = cls.env['service.line'].create({
            'service_type_id': cls.service_type.id,
        })

        # Service package
        cls.package = cls.env['service.package'].create({
            'name': 'Basic Service',
            'total': 1000,
            'service_ids': [(4, cls.package_line.id)]
        })

        cls.booking = cls.env['service.booking'].create({
            'vehicle_no': 'KL01AB1234',
            'partner_id': cls.partner.id,
            'model_id': cls.vehicle_model.id,
            'date': '2026-05-27',
            'service_package_id': cls.package.id,
            'company_id': cls.env.company.id
        })

    def test_reference_sequence(self):
        self.assertNotEqual(

            self.booking.reference_no,
            "New"
        )
        self.assertTrue(
            self.booking.reference_no
        )

    def test_action_confirm(self):
        self.booking.action_confirm()
        self.assertEqual(
            self.booking.state,
            'confirm'
        )
        worksheet_count = self.env[
            'service.worksheet'
        ].search_count([
            ('service_booking_id', '=', self.booking.id)
        ])
        self.assertGreater(
            worksheet_count,0
        )

    def test_create_invoice(self):
        self.booking.action_create_invoice()
        invoice = self.env[
            'account.move'
        ].search([
            ('invoice_origin', '=', self.booking.reference_no)
        ])
        self.assertTrue(invoice)
        self.assertEqual(
            self.booking.state,
            'to_invoice'
        )
        self.assertEqual(
            invoice.partner_id.id,
            self.partner.id
        )

    def test_invoice_count(self):
        self.booking.action_create_invoice()
        self.booking._compute_invoice_count()
        self.assertEqual(
            self.booking.invoice_count,
            1
        )

    def test_unlink_confirmed_booking(self):
        self.booking.action_confirm()
        with self.assertRaises(UserError):
            self.booking.unlink()

    def test_unlink_draft_booking(self):
        booking = self.env['service.booking'].create({
            'vehicle_no': 'KL01XY1111',
            'partner_id': self.partner.id,
            'model_id': self.vehicle_model.id,
            'date': '2026-05-27',
            'service_package_id': self.package.id,
            'company_id': self.env.company.id
        })
        booking.unlink()
        result = self.env['service.booking'].search([
            ('id', '=', booking.id)
        ])
        self.assertFalse(result)


