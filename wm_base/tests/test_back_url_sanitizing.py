"""The signature editor's back_url must never be an open redirect or script."""
from odoo.tests import TransactionCase, tagged

from odoo.addons.wm_base.controllers.portal import _safe_back_url, _safe_int_str


@tagged('post_install', '-at_install')
class TestBackUrlSanitizing(TransactionCase):

    def test_only_backend_paths_are_accepted(self):
        self.assertEqual(_safe_back_url('/web#id=1&model=x&view_type=form'), '/web#id=1&model=x&view_type=form')
        self.assertEqual(_safe_back_url('/odoo/action-12'), '/odoo/action-12')
        for evil in ('//evil.com', 'https://evil.com', 'javascript:alert(1)',
                     '/web"onclick="x', '/web<script>', '/web\\evil', ''):
            self.assertEqual(_safe_back_url(evil), '', evil)

    def test_ids_are_digits_only(self):
        self.assertEqual(_safe_int_str('42'), '42')
        self.assertEqual(_safe_int_str('4"><x'), '')
        self.assertEqual(_safe_int_str(None), '')
