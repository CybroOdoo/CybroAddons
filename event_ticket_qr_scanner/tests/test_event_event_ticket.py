# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from odoo import models


@tagged('post_install', '-at_install')
class TestEventEventTicket(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestEventEventTicket, cls).setUpClass()
        # Set up a test event
        cls.event_type = cls.env['event.type'].create({
            'name': 'Test Event Type',
        })
        cls.event = cls.env['event.event'].create({
            'name': 'Test QR Code Event',
            'event_type_id': cls.event_type.id,
            'date_begin': '2026-07-01 10:00:00',
            'date_end': '2026-07-01 18:00:00',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Event Ticket Product',
            'type': 'service',
        })

    def test_create_generates_qr_code(self):
        """Test that creating a new ticket automatically generates a QR code."""
        ticket = self.env['event.event.ticket'].create({
            'name': 'VIP Ticket',
            'event_id': self.event.id,
            'product_id': self.product.id,
            'price': 150.0,
        })
        self.assertTrue(ticket.ticket_qr_code_image,
                        "QR code should be generated on creation of the ticket.")

    def test_write_regenerates_qr_code(self):
        """Test that writing to a ticket regenerates the QR code if it is missing."""
        ticket = self.env['event.event.ticket'].create({
            'name': 'Standard Ticket',
            'event_id': self.event.id,
            'product_id': self.product.id,
            'price': 50.0,
        })
        
        # To simulate a missing QR code, we must bypass the overridden `write` method
        # directly, so it does not intercept our attempt to set it to False.
        # We do this by invoking the base ORM Model.write.
        models.Model.write(ticket, {'ticket_qr_code_image': False})
        
        self.assertFalse(ticket.ticket_qr_code_image)
        
        # Trigger a normal write operation to see if it regenerates correctly
        ticket.write({'name': 'Updated Standard Ticket'})
        self.assertTrue(ticket.ticket_qr_code_image,
                        "QR code should be regenerated if missing during a write.")

    def test_generate_ticket_qr(self):
        """Test the generation logic directly."""
        ticket = self.env['event.event.ticket'].create({
            'name': 'Test Ticket',
            'event_id': self.event.id,
            'product_id': self.product.id,
            'price': 100.0,
        })
        # Call the method directly
        qr_image = ticket.generate_ticket_qr(ticket.id)
        self.assertTrue(qr_image,
                        "generate_ticket_qr should return the base64 encoded QR image.")
