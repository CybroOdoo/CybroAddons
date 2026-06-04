# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import ValidationError


def _mock_response(status_code=200, json_data=None, text=''):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = text
    return resp


@tagged('post_install', '-at_install', 'odoo_google_contact_integration')
class TestResPartnerFields(TransactionCase):
    """Field-presence and metadata tests for res.partner extension."""

    def test_required_partner_fields_exist_and_readonly(self):
        """Check that required fields exist on res.partner and readonly fields are correctly configured."""
        required_fields = [
            'google_resource',
            'google_etag',
            'first_name',
            'last_name',
        ]
        readonly_fields = [
            'google_resource',
            'google_etag',
        ]
        for field in required_fields:
            with self.subTest(field=field, check='exists'):
                self.assertIn(field, self.env['res.partner']._fields)

        for field in readonly_fields:
            with self.subTest(field=field, check='readonly'):
                self.assertTrue(self.env['res.partner']._fields[field].readonly)


@tagged('post_install', '-at_install', 'odoo_google_contact_integration')
class TestResPartnerExport(TransactionCase):
    """Tests for action_export_google_contacts."""

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.company.contact_company_access_token = 'test-token'
        self.partner = self.env['res.partner'].create({
            'name': 'Export Partner',
            'first_name': 'Export',
            'last_name': 'Partner',
            'email': 'export@example.com',
            'phone': '+9100000001',
        })

    def _call_export(self, partners):
        return partners.with_context(
            active_ids=partners.ids, uid=self.env.uid
        ).action_export_google_contacts()

    # ------------------------------------------------------------------
    # Export new contact (no google_etag → POST createContact)
    # ------------------------------------------------------------------

    @patch('odoo.addons.odoo_google_contact_integration.models.res_partner.requests.post')
    def test_export_new_posts_to_create_endpoint(self, mock_post):
        """New partner (no etag) must POST to people:createContact."""
        mock_post.return_value = _mock_response(
            json_data={'resourceName': 'people/c1', 'etag': 'etag1'})
        self._call_export(self.partner)
        call_url = mock_post.call_args[0][0]
        self.assertIn('createContact', call_url)

    @patch('odoo.addons.odoo_google_contact_integration.models.res_partner.requests.post')
    def test_export_new_stores_resource_and_etag(self, mock_post):
        """After a successful create, partner must store google_resource and google_etag."""
        mock_post.return_value = _mock_response(
            json_data={'resourceName': 'people/c42', 'etag': 'etag42'})
        self._call_export(self.partner)
        self.assertEqual(self.partner.google_resource, 'people/c42')
        self.assertEqual(self.partner.google_etag, 'etag42')


    @patch('odoo.addons.odoo_google_contact_integration.models.res_partner.requests.post')
    def test_export_new_error_message_contains_api_error(self, mock_post):
        """ValidationError message must contain the API error text."""
        mock_post.return_value = _mock_response(
            status_code=400, text='Bad Request Detail')
        with self.assertRaises(ValidationError) as ctx:
            self._call_export(self.partner)
        self.assertIn('Bad Request Detail', str(ctx.exception))

    @patch('odoo.addons.odoo_google_contact_integration.models.res_partner.requests.post')
    def test_export_new_sends_name_in_payload(self, mock_post):
        """Payload must include givenName from first_name (or name fallback)."""
        mock_post.return_value = _mock_response(
            json_data={'resourceName': 'people/c1', 'etag': 'e1'})
        self._call_export(self.partner)
        payload = mock_post.call_args[1].get('json') or {}
        given = payload.get('names', [{}])[0].get('givenName', '')
        self.assertEqual(given, 'Export')

    @patch('odoo.addons.odoo_google_contact_integration.models.res_partner.requests.post')
    def test_export_uses_bearer_token(self, mock_post):
        """Export must send the company access token as Bearer."""
        mock_post.return_value = _mock_response(
            json_data={'resourceName': 'people/c1', 'etag': 'e1'})
        self._call_export(self.partner)
        headers = mock_post.call_args[1].get('headers') or {}
        self.assertIn('test-token', headers.get('Authorization', ''))

    # ------------------------------------------------------------------
    # Export existing contact (has google_etag → PATCH updateContact)
    # ------------------------------------------------------------------

    @patch('odoo.addons.odoo_google_contact_integration.models.res_partner.requests.patch')
    def test_export_existing_patches_update_endpoint(self, mock_patch):
        """Partner with etag must PATCH to updateContact URL."""
        self.partner.sudo().write({
            'google_resource': 'people/existing1',
            'google_etag': 'etag_old',
        })
        mock_patch.return_value = _mock_response(
            json_data={'resourceName': 'people/existing1', 'etag': 'etag_new'})
        self._call_export(self.partner)
        call_url = mock_patch.call_args[0][0]
        self.assertIn('updateContact', call_url)
        self.assertIn('existing1', call_url)

    @patch('odoo.addons.odoo_google_contact_integration.models.res_partner.requests.patch')
    def test_export_existing_updates_etag(self, mock_patch):
        """After a successful update, etag must be refreshed from the response."""
        self.partner.sudo().write({
            'google_resource': 'people/existing2',
            'google_etag': 'old_etag',
        })
        mock_patch.return_value = _mock_response(
            json_data={'resourceName': 'people/existing2', 'etag': 'fresh_etag'})
        self._call_export(self.partner)
        self.assertEqual(self.partner.google_etag, 'fresh_etag')

    @patch('odoo.addons.odoo_google_contact_integration.models.res_partner.requests.patch')
    def test_export_existing_raises_on_api_error(self, mock_patch):
        """Non-200 on update must raise ValidationError."""
        self.partner.sudo().write({
            'google_resource': 'people/existing3',
            'google_etag': 'etag3',
        })
        mock_patch.return_value = _mock_response(
            status_code=404, text='Not Found')
        with self.assertRaises(ValidationError):
            self._call_export(self.partner)

    # ------------------------------------------------------------------
    # Batch export
    # ------------------------------------------------------------------

    @patch('odoo.addons.odoo_google_contact_integration.models.res_partner.requests.post')
    def test_export_batch_calls_api_per_partner(self, mock_post):
        """Export on multiple partners must call the API once per partner."""
        mock_post.return_value = _mock_response(
            json_data={'resourceName': 'people/cx', 'etag': 'ex'})
        p2 = self.env['res.partner'].create({
            'name': 'Second Partner',
            'email': 'second@example.com',
        })
        batch = self.partner | p2
        batch.with_context(active_ids=batch.ids,
                           uid=self.env.uid).action_export_google_contacts()
        self.assertEqual(mock_post.call_count, 2)

    # ------------------------------------------------------------------
    # Name fallback: first_name absent → use name
    # ------------------------------------------------------------------

    @patch('odoo.addons.odoo_google_contact_integration.models.res_partner.requests.post')
    def test_export_uses_name_when_no_first_name(self, mock_post):
        """givenName must fall back to partner.name when first_name is empty."""
        partner = self.env['res.partner'].create({
            'name': 'NoFirstName Partner',
            'email': 'nofirst@example.com',
        })
        mock_post.return_value = _mock_response(
            json_data={'resourceName': 'people/cx', 'etag': 'ex'})
        partner.with_context(active_ids=partner.ids,
                             uid=self.env.uid).action_export_google_contacts()
        payload = mock_post.call_args[1].get('json') or {}
        given = payload.get('names', [{}])[0].get('givenName', '')
        self.assertEqual(given, 'NoFirstName Partner')


@tagged('post_install', '-at_install', 'odoo_google_contact_integration')
class TestResPartnerDeleteGoogle(TransactionCase):
    """Tests for action_delete_google_contact."""

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.company.contact_company_access_token = 'del-token'

    def _make_partner(self, resource='people/del1', etag='etag_del'):
        return self.env['res.partner'].create({
            'name': 'Delete Me',
            'google_resource': resource,
            'google_etag': etag,
        })

    def _call_delete(self, partners):
        return partners.with_context(
            active_ids=partners.ids, uid=self.env.uid
        ).action_delete_google_contact()

    @patch('odoo.addons.odoo_google_contact_integration.models.res_partner.requests.delete')
    def test_delete_removes_partner_on_200(self, mock_del):
        """A 200 response must delete the local partner record."""
        mock_del.return_value = _mock_response(status_code=200)
        partner = self._make_partner()
        partner_id = partner.id
        self._call_delete(partner)
        self.assertFalse(self.env['res.partner'].browse(partner_id).exists())

    @patch('odoo.addons.odoo_google_contact_integration.models.res_partner.requests.delete')
    def test_delete_clears_resource_on_404(self, mock_del):
        """A 404 response (already deleted in Google) must clear local google_resource."""
        mock_del.return_value = _mock_response(status_code=404)
        partner = self._make_partner(resource='people/gone1')
        self._call_delete(partner)
        self.assertFalse(partner.google_resource)
        self.assertFalse(partner.google_etag)

    @patch('odoo.addons.odoo_google_contact_integration.models.res_partner.requests.delete')
    def test_delete_404_does_not_unlink_partner(self, mock_del):
        """A 404 must clear references but NOT delete the local partner."""
        mock_del.return_value = _mock_response(status_code=404)
        partner = self._make_partner(resource='people/gone2')
        partner_id = partner.id
        self._call_delete(partner)
        self.assertTrue(self.env['res.partner'].browse(partner_id).exists())

    @patch('odoo.addons.odoo_google_contact_integration.models.res_partner.requests.delete')
    def test_delete_raises_on_api_error(self, mock_del):
        """A non-200/404 response must raise ValidationError."""
        mock_del.return_value = _mock_response(
            status_code=500, text='Internal Server Error')
        partner = self._make_partner()
        with self.assertRaises(ValidationError):
            self._call_delete(partner)

    @patch('odoo.addons.odoo_google_contact_integration.models.res_partner.requests.delete')
    def test_delete_uses_bearer_token(self, mock_del):
        """Delete request must use Bearer token from company access token."""
        mock_del.return_value = _mock_response(status_code=200)
        partner = self._make_partner()
        self._call_delete(partner)
        headers = mock_del.call_args[1].get('headers') or {}
        self.assertIn('del-token', headers.get('Authorization', ''))

    @patch('odoo.addons.odoo_google_contact_integration.models.res_partner.requests.delete')
    def test_delete_url_contains_resource_name(self, mock_del):
        """Delete URL must include the partner's google_resource."""
        mock_del.return_value = _mock_response(status_code=200)
        partner = self._make_partner(resource='people/specific_resource')
        self._call_delete(partner)
        call_url = mock_del.call_args[0][0]
        self.assertIn('specific_resource', call_url)

    @patch('odoo.addons.odoo_google_contact_integration.models.res_partner.requests.delete')
    def test_delete_batch_processes_all_partners(self, mock_del):
        """Batch delete must call the API for each partner that has a resource."""
        mock_del.return_value = _mock_response(status_code=200)
        p1 = self._make_partner(resource='people/b1', etag='e1')
        p2 = self._make_partner(resource='people/b2', etag='e2')
        batch = p1 | p2
        batch.with_context(active_ids=batch.ids,
                           uid=self.env.uid).action_delete_google_contact()
        self.assertEqual(mock_del.call_count, 2)
