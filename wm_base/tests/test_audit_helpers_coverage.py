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
from unittest.mock import patch

from odoo import models
from odoo.addons.wm_base.models import wm_audit_mixin
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAuditHelpers(TransactionCase):
    """Display helpers of the audit trail and the record names of the logs."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Audit Helper Partner', 'comment': '<p>Hello <b>world</b></p>'})
        cls.child = cls.env['res.partner'].create({'name': 'Audit Child', 'parent_id': cls.partner.id})
        cls.value_of = staticmethod(type(cls.env['wm.audit.mixin'])._get_audit_value)

    def _value(self, field_name, value):
        return self.value_of(self.partner, field_name, value)

    def test_empty_values_are_blank(self):
        for empty in (False, None, ''):
            self.assertEqual(self._value('name', empty), '')

    def test_unknown_field_is_truncated(self):
        self.assertEqual(self._value('no_such_field', 'x' * 300), 'x' * 197 + '...')
        self.assertEqual(self._value('no_such_field', 'short'), 'short')

    def test_binary_field(self):
        raw = base64.b64encode(b'x' * 4096)
        self.assertIn('Binary File', self._value('image_1920', raw))
        self.assertIn('Binary File', self._value('image_1920', b'x' * 2048))
        self.assertIn('0.0 KB', self._value('image_1920', 42))

    def test_html_field(self):
        self.assertEqual(self._value('comment', '<p>Hello <b>world</b></p>'), 'Hello *world*')
        long_text = '<p>%s</p>' % ('word ' * 100)
        self.assertTrue(self._value('comment', long_text).endswith('...'))

    def test_many2one_field(self):
        self.assertEqual(self._value('parent_id', self.partner), self.partner.display_name)
        self.assertEqual(self._value('parent_id', self.partner.id), self.partner.display_name)
        self.assertIn('Deleted', self._value('parent_id', 999999999))
        self.assertIn('Deleted', self._value('parent_id', self.env['res.partner'].browse(999999999)))

    def test_selection_field(self):
        self.assertEqual(self._value('type', 'contact'), 'Contact')
        self.assertEqual(self._value('type', 'unknown_key'), 'unknown_key')

    def test_x2many_and_boolean_fields(self):
        self.assertEqual(self._value('child_ids', self.child), '1 record(s)')
        self.assertEqual(self._value('child_ids', 'raw'), 'raw')
        self.assertEqual(self._value('active', True), 'Yes')
        self.assertEqual(self._value('active', 0.5), 'Yes')

    def test_log_record_names(self):
        model = self.env['ir.model']._get('res.partner')
        for log_model in ('wm.audit.log', 'wm.status.transition.log'):
            vals = {'model_id': model.id, 'res_id': self.partner.id}
            if log_model == 'wm.status.transition.log':
                vals['user_id'] = self.env.user.id
            else:
                vals['action'] = 'write'
            log = self.env[log_model].create(vals)
            self.assertEqual(log.record_name, self.partner.display_name)
            log.invalidate_recordset()
            gone = self.env[log_model].create(dict(vals, res_id=999999999))
            self.assertIn('[Deleted]', gone.record_name)
            bad_model = self.env[log_model].create(dict(vals, model_id=self.env['ir.model']._get('ir.model').id, res_id=0))
            self.assertEqual(bad_model.record_name, 'Unknown')

    def test_value_helpers_survive_unexpected_values(self):
        """A value that cannot be formatted never breaks the audit entry."""
        class BrokenBytes(bytes):
            def __bool__(self):
                return True

            def __len__(self):
                raise ValueError('broken')

        class BrokenSet(set):
            def __bool__(self):
                return True

            def __repr__(self):
                return 'broken-set'

            def __len__(self):
                raise ValueError('broken')

        self.assertEqual(self._value('image_1920', BrokenBytes(b'abc')), '[Binary File]')
        with patch.object(wm_audit_mixin, 'html2plaintext', side_effect=ValueError('broken')):
            self.assertEqual(self._value('comment', '<p>text</p>'), '<p>text</p>')
        self.assertEqual(self._value('parent_id', 'not-an-id'), 'not-an-id')
        with patch.object(type(self.partner._fields['type']), '_description_selection',
                          side_effect=ValueError('broken')):
            self.assertEqual(self._value('type', 'contact'), 'contact')
        self.assertEqual(self._value('child_ids', BrokenSet({1})), 'broken-set')

    def test_log_record_name_survives_lookup_errors(self):
        model = self.env['ir.model']._get('res.partner')
        audit = self.env['wm.audit.log'].create({
            'model_id': model.id, 'res_id': self.partner.id, 'action': 'write'})
        transition = self.env['wm.status.transition.log'].create({
            'model_id': model.id, 'res_id': self.partner.id, 'user_id': self.env.user.id})
        for log in (audit, transition):
            log.invalidate_recordset(['record_name'])
            with patch.object(models.BaseModel, 'exists', side_effect=ValueError('broken')):
                self.assertIn('(%s)' % self.partner.id, log.record_name)
