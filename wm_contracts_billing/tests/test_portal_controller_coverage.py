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
from datetime import timedelta

from odoo import fields
from odoo.http import Request
from odoo.tests import HttpCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'wm_billing')
class TestPortalControllerCoverage(HttpCase):
    """Portal routes: ownership isolation, cancellation rules and service request submission."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.today()
        cls.user = new_test_user(cls.env, login='portal_cov_a', password='portal_cov_a',
                                 groups='base.group_portal')
        cls.other = new_test_user(cls.env, login='portal_cov_b', password='portal_cov_b',
                                  groups='base.group_portal')
        cls.partner = cls.user.partner_id
        cls.point = cls.env['wm.collection.point'].create({'name': 'Portal Cov Site', 'partner_id': cls.partner.id})
        cls.other_point = cls.env['wm.collection.point'].create({
            'name': 'Portal Cov Other Site', 'partner_id': cls.other.partner_id.id})
        cls.sla = cls.env['wm.sla'].create({'name': 'Portal Cov SLA', 'terms_and_conditions': 'T'})

    def _contract(self, state, partner=None):
        return self.env['wm.partner.contract'].create({
            'partner_id': (partner or self.partner).id, 'sla_id': self.sla.id,
            'from_date': self.today, 'to_date': self.today + timedelta(days=90),
            'frequency': 'monthly', 'no_of_frequency': 1, 'billing_basis': 'per_collection',
            'fixed_price': 1.0, 'max_weight': 1.0, 'overweight_price': 1.0, 'state': state})

    def _post(self, url, data=None):
        data = dict(data or {}, csrf_token=Request.csrf_token(self))
        return self.url_open(url, data=data, allow_redirects=False)

    def test_contract_detail_ownership(self):
        mine = self._contract('confirmed')
        draft = self._contract('draft')
        theirs = self._contract('confirmed', partner=self.other.partner_id)
        self.authenticate('portal_cov_a', 'portal_cov_a')
        self.assertEqual(self.url_open('/my/contracts/%s' % mine.id).status_code, 200)
        self.assertEqual(self.url_open('/my/contracts/%s' % draft.id).status_code, 404)
        self.assertEqual(self.url_open('/my/contracts/%s' % theirs.id).status_code, 404)
        self.assertEqual(self.url_open('/my/contracts').status_code, 200)

    def test_cancel_contract_rules(self):
        confirmed = self._contract('confirmed')
        ongoing = self._contract('ongoing')
        theirs = self._contract('confirmed', partner=self.other.partner_id)
        self.authenticate('portal_cov_a', 'portal_cov_a')
        res = self._post('/my/contracts/%s/cancel' % ongoing.id, {'cancel_reason': 'x'})
        self.assertIn('cancel_not_allowed', res.headers['Location'])
        self.assertEqual(ongoing.state, 'ongoing')
        self.assertEqual(self._post('/my/contracts/%s/cancel' % theirs.id).status_code, 404)
        self.assertEqual(theirs.state, 'confirmed')
        res = self._post('/my/contracts/%s/cancel' % confirmed.id, {'cancel_reason': 'Moving'})
        self.assertIn('success=cancelled', res.headers['Location'])
        self.assertEqual(confirmed.state, 'cancelled')

    def test_collection_order_isolation_and_cancel(self):
        order = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id, 'collection_point_id': self.point.id, 'state': 'draft'})
        foreign = self.env['wm.collection.order'].create({
            'partner_id': self.other.partner_id.id, 'collection_point_id': self.other_point.id, 'state': 'draft'})
        self.authenticate('portal_cov_a', 'portal_cov_a')
        self.assertEqual(self.url_open('/my/collection/orders/%s' % foreign.id).status_code, 404)
        self.assertEqual(self.url_open('/my/collection/orders/%s' % order.id).status_code, 200)
        self.assertEqual(self._post('/my/collection/orders/%s/cancel' % foreign.id).status_code, 404)
        self.assertEqual(foreign.state, 'draft')
        res = self._post('/my/collection/orders/%s/cancel' % order.id)
        self.assertEqual(res.status_code, 303)
        self.assertEqual(order.state, 'cancelled')

    def test_submit_service_request(self):
        self.authenticate('portal_cov_a', 'portal_cov_a')
        base = {'request_type': 'extra_pickup', 'collection_point_id': self.point.id,
                'requested_date': str(self.today)}
        Request = self.env['wm.portal.service.request']
        before = Request.search_count([])
        res = self._post('/my/service-requests/submit', base)
        self.assertIn('success=submitted', res.headers['Location'])
        req = Request.search([('partner_id', '=', self.partner.id)], limit=1)
        self.assertEqual(req.state, 'submitted')
        # Foreign site, missing fields, bad type, bad date range
        for bad in (dict(base, collection_point_id=self.other_point.id),
                    {'request_type': 'extra_pickup'},
                    dict(base, request_type='bogus'),
                    dict(base, requested_date='not-a-date'),
                    dict(base, hold_start_date='2030-02-02', hold_end_date='2030-01-01')):
            res = self._post('/my/service-requests/submit', bad)
            self.assertIn('error=', res.headers['Location'], bad)
        self.assertEqual(Request.search_count([]), before + 1)

    def test_service_request_detail_and_cancel(self):
        Request = self.env['wm.portal.service.request']
        vals = {'collection_point_id': self.point.id, 'request_type': 'container_swap',
                'requested_date': self.today}
        mine = Request.create(dict(vals, partner_id=self.partner.id))
        mine.action_submit()
        theirs = Request.create({'partner_id': self.other.partner_id.id, 'request_type': 'container_swap',
                                 'collection_point_id': self.other_point.id, 'requested_date': self.today})
        self.authenticate('portal_cov_a', 'portal_cov_a')
        self.assertEqual(self.url_open('/my/service-requests/%s' % theirs.id).status_code, 404)
        self.assertEqual(self.url_open('/my/service-requests/%s' % mine.id).status_code, 200)
        self.assertEqual(self._post('/my/service-requests/%s/cancel' % theirs.id).status_code, 404)
        self._post('/my/service-requests/%s/cancel' % mine.id)
        self.assertEqual(mine.state, 'cancelled')
        self.assertEqual(self.url_open('/my/service-requests').status_code, 200)
