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
from odoo import fields
from odoo.tests import HttpCase, new_test_user, tagged

JS_TOGGLE = r"""
(async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const waitFor = async (cond, m, ms = 10000) => {
        const t = Date.now();
        while (Date.now() - t < ms) { if (cond()) { return; } await sleep(50); }
        throw new Error('timeout waiting for: ' + m);
    };
    const shown = (id) => !document.getElementById(id).classList.contains('d-none');
    try {
        const select = document.getElementById('request_type');
        // the interaction starts after the public root is ready
        await waitFor(() => !shown('field_container_type') && shown('field_category'), 'initial state');
        const expectations = {
            extra_pickup: {field_category: true, field_container_type: false, field_requested_date: true, field_service_hold_dates: false},
            container_swap: {field_category: false, field_container_type: true, field_requested_date: true, field_service_hold_dates: false},
            missed_collection: {field_category: false, field_container_type: false, field_requested_date: true, field_service_hold_dates: false},
            service_hold: {field_category: false, field_container_type: false, field_requested_date: false, field_service_hold_dates: true},
        };
        for (const [type, fields] of Object.entries(expectations)) {
            select.value = type;
            select.dispatchEvent(new Event('change', {bubbles: true}));
            for (const [id, visible] of Object.entries(fields)) {
                await waitFor(() => shown(id) === visible, type + ': ' + id + ' visible=' + visible);
            }
        }
        console.log('test successful');
    } catch (e) {
        console.error('Service request form test failed: ' + e.message);
    }
})();
"""

JS_CONFIRM = r"""
(async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    try {
        const button = document.querySelector('.js_confirm_cancel');
        if (!button) { throw new Error('cancel button missing'); }
        await sleep(1000);  // let the interaction start
        const asked = [];
        window.confirm = (message) => { asked.push(message); return false; };
        const event = new MouseEvent('click', {bubbles: true, cancelable: true});
        button.dispatchEvent(event);
        if (!event.defaultPrevented) { throw new Error('declining must stop the submission'); }
        if (asked.length !== 1 || !asked[0].includes('cancel this service request')) {
            throw new Error('unexpected confirmation: ' + JSON.stringify(asked));
        }
        window.confirm = () => true;
        const accept = new MouseEvent('click', {bubbles: true, cancelable: true});
        button.form.addEventListener('submit', (e) => e.preventDefault(), {once: true});
        button.dispatchEvent(accept);
        if (accept.defaultPrevented) { throw new Error('accepting must not stop the submission'); }
        console.log('test successful');
    } catch (e) {
        console.error('Cancel confirmation test failed: ' + e.message);
    }
})();
"""


@tagged('post_install', '-at_install', 'wm_billing')
class TestPortalInteractions(HttpCase):
    """Portal service request page behaviour implemented as public interactions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(cls.env, login='portal_int_a', password='portal_int_a',
                                 groups='base.group_portal')
        cls.partner = cls.user.partner_id
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'Interaction Site', 'partner_id': cls.partner.id})

    def test_request_type_toggles_form_fields(self):
        self.browser_js('/my/service-requests/new', JS_TOGGLE,
                        ready="document.readyState === 'complete'",
                        login='portal_int_a', timeout=60)

    def test_cancel_asks_for_confirmation(self):
        request = self.env['wm.portal.service.request'].create({
            'partner_id': self.partner.id, 'request_type': 'extra_pickup',
            'collection_point_id': self.point.id, 'requested_date': fields.Date.today(),
            'state': 'submitted'})
        self.browser_js('/my/service-requests/%s' % request.id, JS_CONFIRM,
                        ready="document.readyState === 'complete'",
                        login='portal_int_a', timeout=60)
