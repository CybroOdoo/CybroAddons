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
from odoo.exceptions import AccessError, UserError
from odoo.tests import HttpCase, new_test_user, tagged


class GdprCommon(HttpCase):
    """A GDPR template, a portal customer and a website designer."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['gdpr.template'].search([]).active = False

        def field(name):
            return cls.env['ir.model.fields']._get('res.partner', name)

        cls.template = cls.env['gdpr.template'].create({
            'name': 'Contact Details',
            'description': '<p>Your phone, city and website.</p>',
            'field_ids': [(6, 0, (field('phone') | field('city')
                                  | field('website') | field('country_id')
                                  ).ids)],
        })
        cls.portal_user = new_test_user(
            cls.env, login='gdpr_portal', groups='base.group_portal',
            name='Gina Portal', email='gina@example.com')
        cls.customer = cls.portal_user.partner_id
        cls.customer.write({
            'phone': '+32 555 12 34', 'city': 'Brussels',
            'website': 'https://gina.example.com',
            'country_id': cls.env.ref('base.be').id,
        })
        cls.designer = new_test_user(
            cls.env, login='gdpr_designer',
            groups='base.group_user,website.group_website_designer')

    def _mails(self, gdpr_requests):
        """Return the bodies of the emails queued for the requests."""
        return self.env['mail.mail'].search([
            ('model', '=', 'gdpr.request'),
            ('res_id', 'in', gdpr_requests.ids)]).mapped('body_html')

    def _request(self, req_type, **values):
        return self.env['gdpr.request'].create({
            'partner_id': self.customer.id, 'template_id': self.template.id,
            'req_type': req_type, **values})


@tagged('post_install', '-at_install')
class TestGdprRequest(GdprCommon):

    def test_01_reference(self):
        """Each request gets its own GDPR reference."""
        first, second = self._request('download'), self._request('delete')
        self.assertTrue(first.name.startswith('GDPR'))
        self.assertNotEqual(first.name, second.name)
        self.assertEqual(first.state, 'pending')

    def test_02_confirm_download(self):
        """A designer approves a download request and the customer gets an
        email."""
        gdpr_request = self._request('download').with_user(self.designer)
        gdpr_request.action_confirm_request()
        self.assertEqual(gdpr_request.state, 'done')
        mail = self.env['mail.mail'].search([
            ('model', '=', 'gdpr.request'), ('res_id', '=', gdpr_request.id)])
        self.assertEqual(mail.recipient_ids, self.customer)
        self.assertIn(gdpr_request.name, mail.subject)
        self.assertIn('download your data', mail.body_html)
        with self.assertRaises(UserError):
            gdpr_request.action_cancel_request()

    def test_03_wipe_data(self):
        """Approving a delete request clears only the template fields of
        the customer."""
        gdpr_request = self._request('delete').with_user(self.designer)
        with self.assertRaises(UserError):
            gdpr_request.action_confirm_request()
        with self.assertRaises(UserError):
            self._request('download').action_delete_request()
        gdpr_request.action_delete_request()
        self.assertEqual(gdpr_request.state, 'done')
        self.assertFalse(self.customer.phone or self.customer.city
                         or self.customer.website or self.customer.country_id)
        self.assertEqual(self.customer.email, 'gina@example.com')
        self.assertIn('has been deleted', self._mails(gdpr_request)[0])

    def test_03b_wipe_email_address(self):
        """When the email address is cleared too, the customer is still
        informed at that address."""
        self.template.field_ids = [(4, self.env['ir.model.fields']._get(
            'res.partner', 'email').id)]
        gdpr_request = self._request('delete').with_user(self.designer)
        gdpr_request.action_delete_request()
        self.assertFalse(self.customer.email)
        mail = self.env['mail.mail'].search([
            ('model', '=', 'gdpr.request'), ('res_id', '=', gdpr_request.id)])
        self.assertEqual(mail.email_to, 'gina@example.com')
        self.assertFalse(mail.recipient_ids)
        self.assertIn('has been deleted', mail.body_html)

    def test_04_cancel_without_email(self):
        """Cancelling informs the customer, unless the template does not
        allow messages."""
        gdpr_request = self._request('download')
        gdpr_request.action_cancel_request()
        self.assertIn('has been cancelled', self._mails(gdpr_request)[0])
        self.template.allow_messages = False
        gdpr_request = self._request('delete')
        gdpr_request.action_cancel_request()
        self.assertEqual(gdpr_request.state, 'cancel')
        self.assertFalse(self._mails(gdpr_request))
        self.customer.email = False
        self.template.allow_messages = True
        gdpr_request = self._request('download')
        gdpr_request.action_cancel_request()
        self.assertFalse(self._mails(gdpr_request),
                         "No email for a customer without email address")
        self.assertEqual(self.customer.city, 'Brussels')

    def test_05_gdpr_data(self):
        """The PDF lists each template field with a readable value."""
        data = {item['name']: item['data']
                for item in self._request('download').get_gdpr_data()}
        self.assertEqual(data['City'], 'Brussels')
        self.assertEqual(data['Country'], 'Belgium')
        self.customer.phone = False
        data = {item['name']: item['data']
                for item in self._request('download').get_gdpr_data()}
        self.assertEqual(data['Phone'], 'No data for this field')

    def test_05b_gdpr_data_field_types(self):
        """Boolean, image and selection fields are shown as text."""
        fields = self.env['ir.model.fields']
        employee, image, lang = (fields._get('res.partner', name) for name in (
            'employee', 'image_1920', 'lang'))
        self.template.field_ids = [(4, field.id)
                                   for field in (employee, image, lang)]
        self.customer.write({'employee': True, 'lang': 'en_US',
                             'image_1920': self.customer.avatar_128})

        def data():
            return {item['name']: item['data']
                    for item in self._request('download').get_gdpr_data()}
        self.assertEqual(data()[employee.field_description], 'Yes')
        self.assertEqual(data()[image.field_description], '[Binary Data]')
        self.assertEqual(data()[lang.field_description], 'English (US)')
        self.customer.employee = False
        self.assertEqual(data()[employee.field_description], 'No')

    def test_06_template_fields(self):
        """Only optional, editable contact fields can be used, so a delete
        request never breaks a contact."""
        for model, name in (('res.partner', 'child_ids'),
                            ('res.partner', 'display_name'),
                            ('res.partner', 'name'),
                            ('res.partner', 'active'),
                            ('res.users', 'login')):
            with self.assertRaises(ValueError):
                self.template.field_ids = [
                    (4, self.env['ir.model.fields']._get(model, name).id)]

    def test_07_access(self):
        """Only website designers manage the requests and templates."""
        employee = new_test_user(self.env, login='gdpr_employee',
                                 groups='base.group_user')
        with self.assertRaises(AccessError):
            self._request('download').with_user(employee).read(['name'])
        with self.assertRaises(AccessError):
            self.template.with_user(employee).read(['name'])
        menu = self.env.ref('website_gdpr_odoo.gdpr_main_root_request')
        self.assertIn(menu.id, self.env['ir.ui.menu'].with_user(
            self.designer)._visible_menu_ids())
        self.assertNotIn(menu.id, self.env['ir.ui.menu'].with_user(
            employee)._visible_menu_ids())


@tagged('post_install', '-at_install')
class TestGdprPortal(GdprCommon):

    def _confirm(self, template_id, req_type):
        return self.make_jsonrpc_request('/gdpr_management/confirm', {
            'template_id': template_id, 'req_type': req_type})

    def test_01_portal_page(self):
        """The portal shows the personal data card and page."""
        self.authenticate('gdpr_portal', 'gdpr_portal')
        response = self.url_open('/my/home')
        self.assertIn('/my/data_management', response.text)
        response = self.url_open('/my/data_management')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Contact Details', response.text)
        self.assertNotIn('Lorem', response.text)

    def test_02_create_requests(self):
        """The customer sends download and delete requests for their own
        contact, once while they are pending."""
        self.authenticate('gdpr_portal', 'gdpr_portal')
        self.assertEqual(self._confirm(self.template.id, 'download'),
                         {'status': 'success'})
        self.assertEqual(self._confirm(self.template.id, 'download'),
                         {'status': 'pending'})
        self.assertEqual(self._confirm(self.template.id, 'delete'),
                         {'status': 'success'})
        requests = self.env['gdpr.request'].search(
            [('partner_id', '=', self.customer.id)])
        self.assertEqual(sorted(requests.mapped('req_type')),
                         ['delete', 'download'])
        self.assertEqual(requests.mapped('req_name'), [
            'Contact Details: Delete Data', 'Contact Details: Download Data'])
        self.assertEqual(self._confirm(self.template.id, 'export')['status'],
                         'error')
        self.template.active = False
        self.assertEqual(self._confirm(self.template.id, 'delete')['status'],
                         'error')

    def test_03_download_pdf(self):
        """Only the customer of an approved download request gets its
        PDF."""
        gdpr_request = self._request('download')
        self.authenticate('gdpr_portal', 'gdpr_portal')
        url = f'/gdpr_management/download/{gdpr_request.id}'
        response = self.url_open(url, allow_redirects=False)
        self.assertEqual(response.status_code, 303, "Not approved yet")
        gdpr_request.action_confirm_request()
        response = self.url_open(url)
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')
        self.assertIn(gdpr_request.name, response.headers[
            'Content-Disposition'])
        new_test_user(self.env, login='gdpr_other', groups='base.group_portal')
        self.authenticate('gdpr_other', 'gdpr_other')
        response = self.url_open(url, allow_redirects=False)
        self.assertEqual(response.status_code, 303,
                         "Another customer cannot download the data")

    def test_04_submit_page(self):
        """The confirmation page tells whether the request was sent."""
        self.authenticate('gdpr_portal', 'gdpr_portal')
        self.assertIn('has been sent',
                      self.url_open('/gdpr_management/submit').text)
        self.assertIn('already have the same request', self.url_open(
            '/gdpr_management/submit?status=pending').text)
        self.assertIn('not available anymore', self.url_open(
            '/gdpr_management/submit?status=error').text)

    def test_05_tour(self):
        """A customer requests a download and a delete from the portal."""
        self.start_tour('/my/data_management', 'website_gdpr_portal_tour',
                        login='gdpr_portal')
        requests = self.env['gdpr.request'].search(
            [('partner_id', '=', self.customer.id)])
        self.assertEqual(sorted(requests.mapped('req_type')),
                         ['delete', 'download'])
