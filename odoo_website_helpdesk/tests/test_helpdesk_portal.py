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
from odoo.tests import HttpCase, tagged

from .common import HelpdeskCommon


@tagged('post_install', '-at_install')
class TestHelpdeskPortal(HttpCase, HelpdeskCommon):
    """Website form, customer portal and rating of the tickets"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.params = cls.env['ir.config_parameter'].sudo()
        cls.product = cls.env['product.template'].create(
            {'name': 'Laser Printer', 'sale_ok': True})
        cls.hidden_product = cls.env['product.template'].create(
            {'name': 'Internal Part', 'sale_ok': False})

    def setUp(self):
        super().setUp()
        self.authenticate(None, None)

    def _post_ticket(self, **values):
        """Post the website form of the helpdesk"""
        data = dict({
            'customer_name': 'Web Visitor',
            'email_from': 'visitor@example.com',
            'phone': '+1 555 0100',
            'subject': 'Website issue',
            'description': 'The page does not load',
            'ticket_type_id': str(self.ticket_type.id),
            'category': str(self.category.id),
            'priority': '3',
            'csrf_token': self.csrf_token(),
        }, **values)
        files = values.pop('files', None)
        data.pop('files', None)
        return self.url_open('/website/form/ticket.helpdesk', data=data,
                             files=files).json()

    def test_01_ticket_form_page(self):
        """The form lists the types, and the categories and the products
        when they are enabled"""
        page = self.url_open('/helpdesk_ticket').text
        self.assertIn('name="ticket_type_id"', page)
        self.assertIn(self.ticket_type.name, page)
        self.assertNotIn('name="category"', page)
        self.assertNotIn('Laser Printer', page)
        self.params.set_bool('odoo_website_helpdesk.product_website', True)
        self.env.ref('base.group_user')._apply_group(
            self.env.ref('odoo_website_helpdesk.group_show_category'))
        page = self.url_open('/helpdesk_ticket').text
        self.assertIn('name="category"', page)
        self.assertIn('Laser Printer', page)
        self.assertNotIn('Internal Part', page)

    def test_02_create_ticket_from_website(self):
        """A visitor creates a ticket with attachments, linked to a new
        contact, and the sold products only"""
        self.params.set_bool('odoo_website_helpdesk.product_website', True)
        result = self._post_ticket(
            product=f'{self.product.id},{self.hidden_product.id}',
            files={'ticket_attachment[0][0]': ('log.txt', b'error log',
                                               'text/plain')})
        ticket = self.Ticket.browse(result['id'])
        self.assertEqual(ticket.subject, 'Website issue')
        self.assertEqual(ticket.customer_id.email, 'visitor@example.com')
        self.assertEqual(ticket.customer_id.name, 'Web Visitor')
        self.assertEqual(ticket.ticket_type_id, self.ticket_type)
        self.assertEqual(ticket.category_id, self.category)
        self.assertEqual(ticket.priority, '3')
        self.assertEqual(ticket.product_ids, self.product)
        self.assertEqual(ticket.attachment_ids.name, 'log.txt')
        self.assertEqual(ticket.attachment_ids.file_size, 9)
        # The same email reuses the contact
        second = self.Ticket.browse(self._post_ticket()['id'])
        self.assertEqual(second.customer_id, ticket.customer_id)
        self.assertFalse(second.product_ids)

    def test_03_create_ticket_errors(self):
        """The form answers an error without email, and the logged in
        customer gets the ticket"""
        result = self._post_ticket(email_from='')
        self.assertIn('error', result)
        self.authenticate('hd_portal', 'hd_portal')
        ticket = self.Ticket.browse(self._post_ticket(email_from='')['id'])
        self.assertEqual(ticket.customer_id, self.customer)
        result = self._post_ticket(subject='')
        self.assertIn('error', result)
        result = self._post_ticket(description=' ')
        self.assertIn('error', result)

    def test_04_portal_tickets(self):
        """The customer sees their own tickets only"""
        ticket = self._create_ticket(subject='My printer')
        other = self._create_ticket(customer_id=self.other_customer.id,
                                    subject='Secret issue')
        self.authenticate('hd_portal', 'hd_portal')
        home = self.url_open('/my/home').text
        self.assertIn('/my/tickets', home)
        counters = self.make_jsonrpc_request(
            '/my/counters', {'counters': {'ticket_count': 'service_category'}})
        self.assertEqual(counters['ticket_count'], 1)
        page = self.url_open('/my/tickets').text
        self.assertIn('My printer', page)
        self.assertNotIn('Secret issue', page)
        response = self.url_open(f'/my/tickets/{ticket.id}')
        self.assertIn('The printer does not start', response.text)
        response = self.url_open(f'/my/tickets/{other.id}')
        self.assertNotIn('Secret issue', response.text)
        self.assertTrue(response.url.endswith('/my'))
        response = self.url_open(f'/my/tickets/download/{other.id}')
        self.assertNotEqual(response.headers['Content-Type'],
                            'application/pdf')
        response = self.url_open(f'/my/tickets/download/{ticket.id}')
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')
        self.assertIn(f'Ticket_{ticket.name}.pdf',
                      response.headers['Content-Disposition'])

    def test_05_access_token(self):
        """The link of the emails opens the ticket without login"""
        ticket = self._create_ticket()
        response = self.url_open(f'/my/tickets/{ticket.id}')
        self.assertNotIn('The printer does not start', response.text)
        response = self.url_open(
            f'/my/tickets/{ticket.id}?access_token={ticket._portal_ensure_token()}')
        self.assertIn('The printer does not start', response.text)
        response = self.url_open(f'/my/tickets/{ticket.id}?access_token=wrong')
        self.assertNotIn('The printer does not start', response.text)

    def test_06_search_and_group(self):
        """The customer searches and groups their tickets"""
        self._create_ticket(subject='Printer jam',
                            ticket_type_id=self.ticket_type.id)
        self._create_ticket(subject='Screen flicker',
                            stage_id=self.stage_progress.id)
        self._create_ticket(customer_id=self.other_customer.id,
                            subject='Printer of another customer')
        self.authenticate('hd_portal', 'hd_portal')
        html = self.make_jsonrpc_request('/ticketsearch',
                                         {'search_value': 'printer'})
        self.assertIn('Printer jam', html)
        self.assertNotIn('Screen flicker', html)
        self.assertNotIn('another customer', html)
        html = self.make_jsonrpc_request('/ticketgroupby',
                                         {'search_value': '1'})
        self.assertIn(self.stage_progress.name, html)
        self.assertIn(self.stage_inbox.name, html)
        html = self.make_jsonrpc_request('/ticketgroupby',
                                         {'search_value': '2'})
        self.assertIn(self.ticket_type.name, html)
        self.assertIn('No Type', html)
        html = self.make_jsonrpc_request('/ticketgroupby',
                                         {'search_value': '0'})
        self.assertIn('Screen flicker', html)
        self.assertNotIn('another customer', html)

    def test_07_rating(self):
        """The customer rates the closed ticket from the email link"""
        ticket = self._create_ticket()
        ticket.stage_id = self.stage_closed
        token = ticket.access_token
        page = self.url_open(f'/rating/{ticket.id}?access_token={token}').text
        self.assertIn('How did we do?', page)
        response = self.url_open(f'/rating/{ticket.id}?access_token=wrong')
        self.assertNotIn('How did we do?', response.text)
        data = {'csrf_token': self.csrf_token(), 'access_token': token,
                'rating': '9', 'message': 'Bad value'}
        self.url_open(f'/rating/{ticket.id}/submit', data=data)
        self.assertEqual(ticket.customer_rating, '0')
        data.update(rating='5', message='Very fast answer')
        response = self.url_open(f'/rating/{ticket.id}/submit', data=data)
        self.assertIn('Thank you for rating our support', response.text)
        self.assertEqual(ticket.customer_rating, '5')
        self.assertEqual(ticket.review, 'Very fast answer')
        self.assertIn('Very fast answer', ticket.message_ids[0].body)
        data.update(access_token='wrong', rating='1')
        self.url_open(f'/rating/{ticket.id}/submit', data=data)
        self.assertEqual(ticket.customer_rating, '5')

    def test_08_tour_website_ticket(self):
        """A visitor creates a ticket from the Helpdesk page"""
        self.start_tour('/helpdesk_ticket', 'odoo_website_helpdesk_form_tour')
        ticket = self.Ticket.search([('subject', '=', 'Tour printer issue')])
        self.assertEqual(ticket.customer_id.email, 'tour@example.com')

    def test_09_tour_portal_search(self):
        """The customer searches their tickets in the portal"""
        self._create_ticket(subject='Printer jam')
        self._create_ticket(subject='Screen flicker')
        self.start_tour('/my/tickets', 'odoo_website_helpdesk_portal_tour',
                        login='hd_portal')
