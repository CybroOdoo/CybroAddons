# -*- coding: utf-8 -*-
from odoo.tests.common import tagged
from odoo.exceptions import UserError
from odoo import Command
from odoo.addons.mail.models.mail_mail import MailMail
from unittest.mock import patch
from datetime import date, timedelta
from .common import TestConsignmentCommon


@tagged('post_install', '-at_install')
class TestSaleConsignment(TestConsignmentCommon):

    def test_01_create_consignment_order(self):
        """Test creating a consignment order, sequences, pricelists, and remaining quantities."""
        consignment = self.env['sale.consignment'].create({
            'partner_id': self.partner_consignment.id,
            'end_date': date.today() + timedelta(days=10),
            'location_id': self.location_src.id,
            'consignment_line_ids': [
                Command.create({
                    'product_id': self.product_consignment.id,
                    'demand_quantity': 5,
                })
            ]
        })

        # Check sequence generated
        self.assertNotEqual(consignment.name, 'New')
        self.assertTrue(consignment.name)

        # Check pricelist
        self.assertEqual(consignment.pricelist_id, self.partner_consignment.property_product_pricelist)

        # Check counts
        self.assertEqual(consignment.sale_count, 0)
        self.assertEqual(consignment.picking_count, 0)

        # Check line remaining quantity
        line = consignment.consignment_line_ids[0]
        self.assertEqual(line.remaining_quantity, 5)

    def test_02_confirm_consignment_order_error(self):
        """Test confirming consignment raises UserError if no picking type matches."""
        # Archive our custom picking type so no type matches
        self.picking_type.active = False

        consignment = self.env['sale.consignment'].create({
            'partner_id': self.partner_consignment.id,
            'end_date': date.today() + timedelta(days=10),
            'location_id': self.location_src.id,
            'consignment_line_ids': [
                Command.create({
                    'product_id': self.product_consignment.id,
                    'demand_quantity': 5,
                })
            ]
        })

        with self.assertRaises(UserError) as err:
            consignment.action_order_confirm()
        self.assertIn("There is no available Operation type like destination to transit location Please create and try again", err.exception.args[0])

    def test_03_mail_reminder(self):
        """Test mail reminder sends emails for consignments expiring today."""
        # Consignment expiring today
        consignment_today = self.env['sale.consignment'].create({
            'partner_id': self.partner_consignment.id,
            'end_date': date.today(),
            'location_id': self.location_src.id,
        })

        # Consignment expiring in future
        self.env['sale.consignment'].create({
            'partner_id': self.partner_consignment.id,
            'end_date': date.today() + timedelta(days=2),
            'location_id': self.location_src.id,
        })

        # Clean prior emails
        self.env['mail.mail'].search([('subject', '=', 'Reminder: Sale Consignment Date Expired')]).unlink()

        # Run mail update
        with patch.object(MailMail, 'send') as mock_send:
            self.env['sale.consignment'].mail_update_to_salesman()
            # The mail record should still exist because send was mocked
            emails = self.env['mail.mail'].search([('subject', '=', 'Reminder: Sale Consignment Date Expired')])
            self.assertTrue(emails)
            self.assertEqual(emails.email_to, consignment_today.user_id.partner_id.email)
