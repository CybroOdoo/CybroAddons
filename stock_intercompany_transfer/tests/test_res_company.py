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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Test suite for res.company model extensions."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResCompany(TransactionCase):
    """Test suite covering company configuration and message computation for inter-company transfer."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env['res.company'].create({
            'name': 'Intercompany Config Test Company',
        })
        cls.warehouse = cls.env['stock.warehouse'].search([
            ('company_id', '=', cls.company.id)
        ], limit=1)
        if not cls.warehouse:
            cls.warehouse = cls.env['stock.warehouse'].create({
                'name': 'Test Config Warehouse',
                'code': 'TCW',
                'company_id': cls.company.id,
            })

    def test_compute_message_incoming(self):
        """Test _compute_message when apply_transfer_type is incoming."""
        self.company.write({
            'apply_transfer_type': 'incoming',
            'destination_warehouse_id': self.warehouse.id,
        })
        self.company._compute_message()
        expected = (
            f"Create a Delivery Order when a company validates a Receipt Order "
            f"for {self.company.name} using {self.warehouse.name} Warehouse."
        )
        self.assertEqual(self.company.message, expected)

    def test_compute_message_outgoing(self):
        """Test _compute_message when apply_transfer_type is outgoing."""
        self.company.write({
            'apply_transfer_type': 'outgoing',
            'destination_warehouse_id': self.warehouse.id,
        })
        self.company._compute_message()
        expected = (
            f"Create a Receipt Order when a company validates a Delivery Order "
            f"for {self.company.name} using {self.warehouse.name} Warehouse."
        )
        self.assertEqual(self.company.message, expected)

    def test_compute_message_all(self):
        """Test _compute_message when apply_transfer_type is all."""
        self.company.write({
            'apply_transfer_type': 'all',
            'destination_warehouse_id': self.warehouse.id,
        })
        self.company._compute_message()
        expected = (
            f"Create a Delivery Order/Receipt Order when a company validates a "
            f"Receipt/Delivery Order for {self.company.name} using {self.warehouse.name} Warehouse."
        )
        self.assertEqual(self.company.message, expected)

    def test_onchange_inter_company_transfer(self):
        """Test onchange_inter_company_transfer automatically assigns company warehouse."""
        self.company.destination_warehouse_id = False
        self.company.enable_inter_company_transfer = True
        self.company.onchange_inter_company_transfer()
        self.assertEqual(self.company.destination_warehouse_id, self.warehouse)
