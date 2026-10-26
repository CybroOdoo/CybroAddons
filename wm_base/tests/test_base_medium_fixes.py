#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import io
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged
from odoo.tools import mute_logger

from ..controllers import portal
from ..controllers.portal import WmSignaturePortal

# 1x1 transparent PNG
PNG_B64 = ('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA'
           '60e6kgAAAABJRU5ErkJggg==')


def _make_pdf():
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    can = canvas.Canvas(buf, pagesize=(595, 842))
    can.drawString(100, 750, "Medium fixes test document")
    can.showPage()
    can.save()
    return buf.getvalue()


@tagged('post_install', '-at_install', 'wm_base')
class TestBaseMediumFixes(TransactionCase):
    """Regression tests for the wm_base medium-severity fixes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = WmSignaturePortal()
        cls.role_a = cls.env['wm.signature.role'].create({'name': 'Medium Role A'})
        cls.role_b = cls.env['wm.signature.role'].create({'name': 'Medium Role B'})
        cls.pdf_b64 = base64.b64encode(_make_pdf())
        cls.partner_a = cls.env['res.partner'].create({'name': 'Medium Signer A', 'email': 'a.medium@example.com'})
        cls.partner_b = cls.env['res.partner'].create({'name': 'Medium Signer B', 'email': 'b.medium@example.com'})

    def _template(self, with_items=True):
        template = self.env['wm.signature.template'].create({
            'name': 'Medium Template',
            'role_ids': [(6, 0, (self.role_a | self.role_b).ids)],
            'document': self.pdf_b64,
            'document_filename': 'medium.pdf',
        })
        if with_items:
            Item = self.env['wm.signature.item']
            self.item_a = Item.create({'template_id': template.id, 'role_id': self.role_a.id, 'type': 'signature',
                                       'page': 1, 'x': 10, 'y': 70, 'width': 20, 'height': 5})
            self.item_b = Item.create({'template_id': template.id, 'role_id': self.role_b.id, 'type': 'signature',
                                       'page': 1, 'x': 60, 'y': 70, 'width': 20, 'height': 5})
        return template

    def _request(self, template, roles=None):
        roles = roles or [(self.partner_a, self.role_a), (self.partner_b, self.role_b)]
        req = self.env['wm.signature.request'].create({
            'template_id': template.id,
            'signer_ids': [(0, 0, {'partner_id': p.id, 'role_id': r.id}) for p, r in roles],
        })
        req.state = 'sent'
        return req

    def _mock_request(self):
        mock_req = MagicMock()
        mock_req.env = self.env
        mock_req.httprequest.remote_addr = '127.0.0.1'
        mock_req.httprequest.headers = {'User-Agent': 'test'}
        return mock_req

    def _submit(self, signer, filled_fields):
        with patch.object(portal, 'request', self._mock_request()), mute_logger('odoo.addons.wm_base.controllers.portal'):
            return self.controller.signature_submit(signer.access_token, filled_fields)

    # ---- W-06 ---------------------------------------------------------------
    def test_signer_email_edit_does_not_touch_partner(self):
        req = self._request(self._template())
        signer = req.signer_ids.filtered(lambda s: s.partner_id == self.partner_a)
        self.assertEqual(signer.email, 'a.medium@example.com')
        signer.email = 'other.address@example.com'
        self.assertEqual(self.partner_a.email, 'a.medium@example.com')
        self.assertEqual(signer.email, 'other.address@example.com')

    # ---- X-14 ---------------------------------------------------------------
    def test_submit_rejects_unknown_and_foreign_items(self):
        template = self._template()
        req = self._request(template)
        signer_a = req.signer_ids.filtered(lambda s: s.role_id == self.role_a)
        item_count = len(template.item_ids)
        # Unknown id: no item created, not signed
        res = self._submit(signer_a, [{'item_id': 987654321, 'signature': PNG_B64}])
        self.assertFalse(res['success'])
        # Synthetic id is only valid for templates without items
        res = self._submit(signer_a, [{'item_id': WmSignaturePortal.SYNTHETIC_ITEM_ID, 'signature': PNG_B64}])
        self.assertFalse(res['success'])
        # Another role's item
        res = self._submit(signer_a, [{'item_id': self.item_b.id, 'signature': PNG_B64}])
        self.assertFalse(res['success'])
        self.assertEqual(len(template.item_ids), item_count)
        self.assertEqual(signer_a.state, 'sent')

    def test_submit_requires_a_signature(self):
        req = self._request(self._template())
        signer_a = req.signer_ids.filtered(lambda s: s.role_id == self.role_a)
        self.assertFalse(self._submit(signer_a, [])['success'])
        self.assertFalse(self._submit(signer_a, [{'item_id': self.item_a.id, 'signature': ''}])['success'])
        self.assertEqual(signer_a.state, 'sent')

    def test_submit_valid_signature_and_certificate(self):
        """Valid signing still works end to end (also covers the odoo.tools.pdf switch)."""
        req = self._request(self._template())
        signer_a = req.signer_ids.filtered(lambda s: s.role_id == self.role_a)
        signer_b = req.signer_ids - signer_a
        res = self._submit(signer_a, [{'item_id': self.item_a.id, 'signature': 'data:image/png;base64,' + PNG_B64}])
        self.assertTrue(res['success'], res)
        self.assertEqual(signer_a.state, 'signed')
        res = self._submit(signer_b, [{'item_id': self.item_b.id, 'signature': PNG_B64}])
        self.assertTrue(res['success'], res)
        self.assertEqual(req.state, 'signed')
        self.assertTrue(req.signed_document)
        self.assertTrue(base64.b64decode(req.signed_document).startswith(b'%PDF'))

    def test_synthetic_item_created_once_for_itemless_template(self):
        template = self._template(with_items=False)
        req = self._request(template, roles=[(self.partner_a, self.role_a)])
        sid = WmSignaturePortal.SYNTHETIC_ITEM_ID
        res = self._submit(req.signer_ids, [
            {'item_id': sid, 'signature': PNG_B64},
            {'item_id': sid, 'signature': PNG_B64},
        ])
        self.assertTrue(res['success'], res)
        self.assertEqual(len(template.item_ids), 1)
        self.assertEqual(template.item_ids.type, 'signature')

    # ---- X-15 ---------------------------------------------------------------
    def test_signature_users_cannot_edit_template_items(self):
        template = self._template()
        for group in ('wm_base.group_signature_user', 'wm_base.group_wm_driver'):
            user = new_test_user(self.env, login='medium_%s' % group.split('.')[1], groups=group)
            items = template.item_ids.with_user(user)
            items.check_access('read')
            with self.assertRaises(AccessError):
                items.write({'x': 1.0})
            with self.assertRaises(AccessError):
                items.unlink()

    # ---- V-16 ---------------------------------------------------------------
    def test_category_uniqueness_is_per_company(self):
        Category = self.env['wm.waste.category']
        company_b = self.env['res.company'].create({'name': 'Medium Company B'})
        Category.create({'name': 'Medium Glass', 'code': 'MDGL', 'company_id': self.env.company.id})
        # Same name/code in another company is fine
        other = Category.create({'name': 'Medium Glass', 'code': 'MDGL', 'company_id': company_b.id})
        self.assertTrue(other)
        # Duplicate within the same company (case-insensitive) is not
        with self.assertRaises(ValidationError):
            Category.create({'name': 'medium glass', 'company_id': company_b.id})
        # A shared category clashes with company ones
        with self.assertRaises(ValidationError):
            Category.create({'name': 'Medium Glass', 'company_id': False})

    def test_category_sql_constraints_include_company(self):
        self.env.cr.execute("""
            SELECT pg_get_constraintdef(oid) FROM pg_constraint
            WHERE conrelid = 'wm_waste_category'::regclass AND contype = 'u'
        """)
        definitions = [row[0] for row in self.env.cr.fetchall()]
        self.assertTrue(definitions)
        for definition in definitions:
            self.assertIn('company_id', definition)

    # ---- W-05 / X-11 ----------------------------------------------------------
    def test_dashboard_excludes_billed_orders_from_revenue(self):
        """Only orders billed by a POSTED invoice leave order revenue (see
        wm_contracts_billing/tests/test_billing_decisions.py); the is_billed
        flag alone (no posted invoice) no longer excludes an order."""
        if 'wm.collection.order' not in self.env:
            self.skipTest('wm_collection not installed')
        Order = self.env['wm.collection.order']
        if 'is_billed' not in Order._fields:
            self.skipTest('no billing flag')
        category = self.env['wm.waste.category'].create({'name': 'Medium Dash Cat', 'code': 'MDDC', 'price': 2.0})
        partner = self.env['res.partner'].create({'name': 'Medium Dash Customer'})
        before = self.env['wm.dashboard'].get_dashboard_data('today')
        orders = Order
        for _i in range(2):
            orders |= Order.create({
                'partner_id': partner.id,
                'scheduled_start': fields.Datetime.now(),
                'order_line_ids': [(0, 0, {'category_id': category.id, 'weight': 50.0, 'price': 2.0})],
            })
        orders.sudo().with_context(programmatic_state_change=True).write({'state': 'completed'})
        orders[0].sudo().write({'is_billed': True})
        orders.flush_recordset()
        after = self.env['wm.dashboard'].get_dashboard_data('today')
        expected_amount = sum(orders.mapped('total_amount'))
        self.assertTrue(expected_amount)
        self.assertAlmostEqual(after['revenue_collection'] - before['revenue_collection'], expected_amount, places=2)
        self.assertEqual(after['completed_count'] - before['completed_count'], 2)

    def test_dashboard_category_counts_are_company_scoped(self):
        company_b = self.env['res.company'].create({'name': 'Medium Dash Company B'})
        before = self.env['wm.dashboard'].get_dashboard_data('today')['total_categories']
        self.env['wm.waste.category'].create({'name': 'Medium Other Co Cat', 'company_id': company_b.id})
        after = self.env['wm.dashboard'].with_context(allowed_company_ids=[self.env.company.id]) \
            .get_dashboard_data('today')['total_categories']
        self.assertEqual(before, after)

    def test_dashboard_reports_no_ratio_without_data(self):
        """Ratios with nothing to measure are None (shown as '—'), never 0%."""
        data = self.env['wm.dashboard'].get_dashboard_data('today')
        if not data['inspection_passed'] and not data['inspection_failed']:
            self.assertIsNone(data['inspection_pass_rate'])
        if not data['efficiency_on_time_ids'] and not data['efficiency_late_ids']:
            self.assertIsNone(data['on_time_pct'])
        self.assertEqual(data['currency_id'], self.env.company.currency_id.id)
        self.assertNotIn('currency_symbol', data)

    def test_dashboard_stream_distribution_is_never_material_counts(self):
        """Without collected tonnage the stream chart gets no data rather than
        catalogue material counts passed off as kilograms."""
        if 'wm.collection.order' in self.env and self.env['wm.collection.order'].search_count(
                [('order_line_ids', '!=', False)]):
            self.skipTest('collection data present')
        self.assertTrue(self.env['product.template'].search_count([('is_waste_material', '=', True)]))
        data = self.env['wm.dashboard'].get_dashboard_data('today')
        self.assertEqual(data['stream_distribution'], [])

    def test_dashboard_awaiting_signature_counts_completed_orders_only(self):
        if 'wm.collection.order' not in self.env:
            self.skipTest('wm_collection not installed')
        Order = self.env['wm.collection.order']
        partner = self.env['res.partner'].create({'name': 'Awaiting Signature Customer'})
        before = self.env['wm.dashboard'].get_dashboard_data('today')['awaiting_signature_count']
        orders = Order.create([{'partner_id': partner.id} for _i in range(7)])
        orders[:6].sudo().with_context(programmatic_state_change=True).write({'state': 'completed'})
        orders[6].sudo().with_context(programmatic_state_change=True).write({'state': 'dispatched'})
        data = self.env['wm.dashboard'].get_dashboard_data('today')
        self.assertEqual(data['awaiting_signature_count'] - before, 6)
        self.assertLessEqual(len(data['open_manifests']), 5)

    def test_waste_category_has_no_invented_co2_factor(self):
        category = self.env['wm.waste.category'].create({'name': 'No Factor Cat', 'code': 'NOFAC'})
        self.assertEqual(category.warm_factor_co2, 0.0)
