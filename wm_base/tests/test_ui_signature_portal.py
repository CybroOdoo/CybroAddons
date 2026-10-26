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
from odoo.tests.common import HttpCase, new_test_user, tagged

PORTAL_JS = r"""
(async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const waitFor = async (cond, m, ms = 15000) => {
        const t = Date.now();
        while (Date.now() - t < ms) { if (await cond()) { return; } await sleep(50); }
        throw new Error('timeout waiting for: ' + m);
    };
    const assert = (c, m) => { if (!c) { throw new Error(m); } };
    const $ = (id) => document.getElementById(id);
    const mouse = (el, type, x, y) => el.dispatchEvent(new MouseEvent(type, {
        bubbles: true, cancelable: true, clientX: x, clientY: y}));
    try {
        window.alert = (msg) => { throw new Error('unexpected alert: ' + msg); };
        // Keep the page on the same URL after a successful submission so that
        // the result can still be reported; the redirect target is checked.
        const submitted = {};
        const submission = new Promise((resolve, reject) => Object.assign(submitted, {resolve, reject}));
        const realFetch = window.fetch.bind(window);
        window.fetch = async (url, opts) => {
            const response = await realFetch(url, opts);
            if (String(url).includes('/wm_signature/sign/submit')) {
                const data = await response.clone().json();
                if (data.result && data.result.success
                        && String(data.result.redirect_url).includes('/wm_signature/sign/thankyou')) {
                    data.result.redirect_url = '#submitted';
                    submitted.resolve(data.result);
                } else {
                    submitted.reject(new Error('submit failed: ' + JSON.stringify(data)));
                }
                return new Response(JSON.stringify(data), {status: 200,
                    headers: {'Content-Type': 'application/json'}});
            }
            return response;
        };

        await waitFor(() => document.querySelectorAll('#pdf-sign-overlay .field-box.interactive').length === 2,
            'two interactive fields');
        const boxes = [...document.querySelectorAll('#pdf-sign-overlay .field-box.interactive')];
        assert($('submit-signature').disabled, 'submit starts disabled');
        assert($('signing-progress-text').textContent.includes('Please fill'), 'progress asks to fill fields');

        // --- signature field: drawing pad ------------------------------
        const sigBox = boxes.find((b) => b.textContent.includes('Sign'));
        const textBox = boxes.find((b) => b !== sigBox);
        sigBox.click();
        await waitFor(() => $('signatureModal').classList.contains('show'), 'signature modal');
        await sleep(400);
        assert($('adopt-signature-btn').disabled, 'adopt disabled before drawing');
        const canvas = document.querySelector('#draw-pane canvas');
        const rect = canvas.getBoundingClientRect();
        mouse(canvas, 'mousedown', rect.left + 10, rect.top + 10);
        mouse(canvas, 'mousemove', rect.left + 60, rect.top + 40);
        mouse(canvas, 'mousemove', rect.left + 90, rect.top + 20);
        mouse(canvas, 'mouseup', rect.left + 90, rect.top + 20);
        $('color-blue').click();
        $('color-black').click();
        $('clear-canvas').click();
        await sleep(50);
        assert($('adopt-signature-btn').disabled, 'adopt disabled after clearing the pad');

        // --- type tab ---------------------------------------------------
        $('type-tab').click();
        await waitFor(() => $('type-pane').classList.contains('active'), 'type pane');
        const typed = $('typed-name');
        typed.value = 'Portal Tester';
        typed.dispatchEvent(new Event('input', {bubbles: true}));
        const card = document.querySelector('.font-select-card');
        card.click();
        assert([...document.querySelectorAll('.font-select-card .preview-text')]
            .every((el) => el.textContent === 'Portal Tester'), 'font previews follow the typed name');
        assert(!$('adopt-signature-btn').disabled, 'adopt enabled once a name is typed');

        // --- consent is mandatory ---------------------------------------
        const alerts = [];
        window.alert = (msg) => alerts.push(msg);
        $('adopt-signature-btn').click();
        assert(alerts.length === 1 && alerts[0].includes('agreement'), 'consent is enforced');
        assert(!sigBox.classList.contains('filled'), 'nothing is signed without consent');
        window.alert = (msg) => { throw new Error('unexpected alert: ' + msg); };

        $('consent-check').click();
        $('adopt-signature-btn').click();
        await waitFor(() => sigBox.classList.contains('filled') && sigBox.querySelector('img'),
            'signature adopted');
        assert(sigBox.querySelector('img').src.startsWith('data:image/png'), 'signature is an image');
        await waitFor(() => !$('signatureModal').classList.contains('show'), 'signature modal closed');
        assert($('submit-signature').disabled, 'still disabled with a field left');

        // --- text field -------------------------------------------------
        textBox.click();
        await waitFor(() => $('textInputModal').classList.contains('show'), 'text modal');
        $('inline-text-input').value = 'Hello portal';
        $('save-inline-text').click();
        await waitFor(() => textBox.classList.contains('filled'), 'text saved');
        assert(textBox.textContent.includes('Hello portal'), 'text shown in the box');
        await waitFor(() => !$('submit-signature').disabled, 'submit enabled');
        assert($('signing-progress-text').textContent.includes('All required'), 'progress confirms completion');

        // --- submit -----------------------------------------------------
        $('submit-signature').click();
        const result = await Promise.race([submission, sleep(30000).then(() => {
            throw new Error('submission did not complete');
        })]);
        assert(String(result.redirect_url).includes('#submitted'), 'redirect was captured');
        console.log('test successful');
    } catch (e) {
        console.error('Signature portal test failed: ' + e.message + ' ' + (e.stack || ''));
    }
})();
"""


@tagged('post_install', '-at_install', 'wm_base')
class TestSignaturePortalJs(HttpCase):
    """Drives the public signing page: field overlays, signature pad, typed
    signature, consent check, inline text and the final submission."""

    def setUp(self):
        super().setUp()
        template_id = self.env['wm.signature.template'].create_sample_template()
        self.template = self.env['wm.signature.template'].browse(template_id)
        role = self.template.role_ids[:1]
        self.env['wm.signature.item'].create([
            {'template_id': self.template.id, 'role_id': role.id, 'type': 'signature',
             'page': 1, 'x': 10, 'y': 60, 'width': 30, 'height': 8},
            {'template_id': self.template.id, 'role_id': role.id, 'type': 'text',
             'page': 1, 'x': 55, 'y': 60, 'width': 30, 'height': 5},
        ])
        self.partner = self.env['res.partner'].create({'name': 'Portal Tester', 'email': 'portal@example.com'})
        self.sig_request = self.env['wm.signature.request'].create({
            'template_id': self.template.id,
            'signer_ids': [(0, 0, {'partner_id': self.partner.id, 'role_id': role.id})],
        })
        self.sig_request.action_send()
        self.signer = self.sig_request.signer_ids

    def test_signing_page_flow(self):
        self.browser_js(
            '/wm_signature/sign/%s' % self.signer.access_token, PORTAL_JS,
            ready="document.readyState === 'complete'", timeout=120)
        self.signer.invalidate_recordset()
        self.assertEqual(self.signer.state, 'signed')
        self.assertTrue(self.signer.signature_image, "The captured signature is stored")
        self.assertEqual(self.sig_request.state, 'signed')


EDITOR_JS = r"""
(async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const waitFor = async (cond, m, ms = 15000) => {
        const t = Date.now();
        while (Date.now() - t < ms) { if (await cond()) { return; } await sleep(50); }
        throw new Error('timeout waiting for: ' + m);
    };
    const assert = (c, m) => { if (!c) { throw new Error(m); } };
    const $ = (id) => document.getElementById(id);
    try {
        const alerts = [];
        window.alert = (msg) => alerts.push(msg);
        const overlay = $('pdf-overlay');
        await waitFor(() => overlay && overlay.getBoundingClientRect().width > 0
            && $('pdf-canvas').width > 300, 'pdf rendered');
        await sleep(300);

        const dropField = (type, x, y) => {
            const transfer = new DataTransfer();
            const item = document.querySelector('.draggable-field-item[data-type="' + type + '"]');
            item.dispatchEvent(new DragEvent('dragstart', {dataTransfer: transfer, bubbles: true}));
            const rect = overlay.getBoundingClientRect();
            overlay.dispatchEvent(new DragEvent('drop', {
                dataTransfer: transfer, bubbles: true, cancelable: true,
                clientX: rect.left + rect.width * x, clientY: rect.top + rect.height * y}));
        };
        const boxes = () => [...overlay.querySelectorAll('.field-box')];

        // a drop without a field type is ignored
        overlay.dispatchEvent(new DragEvent('drop', {dataTransfer: new DataTransfer(), bubbles: true, cancelable: true}));
        assert(boxes().length === 0, 'an empty drop creates nothing');

        dropField('signature', 0.2, 0.3);
        dropField('name', 0.5, 0.5);
        dropField('date', 0.5, 0.7);
        assert(boxes().length === 3, 'three fields dropped, got ' + boxes().length);
        assert(boxes()[0].textContent.includes('Signature'), 'signature label shown');
        await sleep(5);

        // selecting a field shows its controls, deleting removes it
        boxes()[2].dispatchEvent(new MouseEvent('mousedown', {bubbles: true, clientX: 10, clientY: 10}));
        document.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
        await waitFor(() => !$('field-selected-controls').classList.contains('d-none'), 'field selected');
        assert(boxes()[2].classList.contains('active'), 'box marked active');
        $('delete-selected-field').click();
        assert(boxes().length === 2, 'selected field deleted');
        assert($('field-selected-controls').classList.contains('d-none'), 'controls hidden again');

        // save
        $('save-template-fields').click();
        await waitFor(() => alerts.length === 1, 'save feedback');
        assert(alerts[0].includes('saved successfully'), 'unexpected feedback: ' + alerts[0]);
        console.log('test successful');
    } catch (e) {
        console.error('Template editor test failed: ' + e.message + ' ' + (e.stack || ''));
    }
})();
"""


THANK_YOU_JS = r"""
(async () => {
    try {
        const text = document.body.textContent;
        if (!text.includes('Tester Name')) { throw new Error('signer name missing'); }
        console.log('test successful');
    } catch (e) {
        console.error('Thank you page test failed: ' + e.message);
    }
})();
"""


@tagged('post_install', '-at_install', 'wm_base')
class TestSignatureTemplateEditorJs(HttpCase):
    """Drives the backend template designer: drop, select, delete and save."""

    def setUp(self):
        super().setUp()
        new_test_user(self.env, login='wm_tpl_admin', groups='base.group_user,wm_base.group_wm_admin')
        self.template = self.env['wm.signature.template'].browse(
            self.env['wm.signature.template'].create_sample_template())

    def test_template_editor_flow(self):
        self.browser_js(
            '/wm_signature/template/edit/%s' % self.template.id, EDITOR_JS,
            ready="document.readyState === 'complete'", login='wm_tpl_admin', timeout=120)
        self.assertEqual(
            sorted(self.template.item_ids.mapped('type')), ['name', 'signature'],
            "The dropped fields are stored on the template")

    def test_thank_you_page(self):
        self.browser_js('/wm_signature/sign/thankyou?name=Tester+Name', THANK_YOU_JS,
                        ready="document.readyState === 'complete'", timeout=60)
