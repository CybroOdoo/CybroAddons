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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestServiceTicket(TransactionCase):
    """Test suite for service ticket report abstract model (service_ticket.py)."""

    def test_01_report_values_structure(self):
        """Verify _get_report_values returns complete report dictionary matching data input."""
        report_model = self.env['report.mobile_service_shop.mobile_service_ticket_template']
        data = {
            'date_today': '2026-10-17 11:00 AM',
            'date_request': '2026-10-16',
            'date_return': '2026-10-21',
            'sev_id': 'SERV/0055',
            'imei_no': '865432098712345',
            'technician': 'Senior Tech',
            'complaint_types': 'Water Damage',
            'complaint_description': 'Phone dropped in water, no power',
            'mobile_brand': 'Apple',
            'model_name': 'iPhone 14',
            'customer_name': 'John Doe',
            'warranty': False,
        }
        res = report_model._get_report_values(docids=[], data=data)
        self.assertEqual(res['sev_id'], 'SERV/0055')
        self.assertEqual(res['customer_name'], 'John Doe')
        self.assertEqual(res['imei_no'], '865432098712345')
        self.assertEqual(res['technician'], 'Senior Tech')
        self.assertEqual(res['complaint_types'], 'Water Damage')
        self.assertEqual(res['complaint_description'], 'Phone dropped in water, no power')
        self.assertEqual(res['mobile_brand'], 'Apple')
        self.assertEqual(res['model_name'], 'iPhone 14')
        self.assertFalse(res['warranty'])
        self.assertIn('terms', res)

    def test_02_report_values_includes_active_terms(self):
        """Verify terms and conditions records in DB are provided to the report context."""
        terms = self.env['terms.conditions'].create({
            'terms_conditions': 'Custom ticket warranty terms and conditions.',
        })
        report_model = self.env['report.mobile_service_shop.mobile_service_ticket_template']
        data = {
            'date_today': '2026-10-17 11:30 AM',
            'date_request': '2026-10-17',
            'date_return': '2026-10-22',
            'sev_id': 'SERV/0056',
            'imei_no': '123456789012345',
            'technician': 'Tech 2',
            'complaint_types': 'Battery',
            'complaint_description': 'Fast discharge',
            'mobile_brand': 'Samsung',
            'model_name': 'S23',
            'customer_name': 'Jane Doe',
            'warranty': True,
        }
        res = report_model._get_report_values(docids=[], data=data)
        self.assertIn(terms.id, res['terms'].ids)
