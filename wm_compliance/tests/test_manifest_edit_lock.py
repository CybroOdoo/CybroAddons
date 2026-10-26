from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'wm_compliance')
class TestManifestEditLock(TransactionCase):
    """Once a manifest leaves draft its header and waste lines cannot be edited,
    in the form and on the server."""

    LOCKED = ('generator_id', 'transporter_id', 'manifest_date', 'disposal_facility_id',
              'compliance_code_ids')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.generator = cls.env['res.partner'].create({'name': 'Lock Generator', 'is_generator': True})
        cls.transporter = cls.env['res.partner'].create({'name': 'Lock Transporter', 'is_transporter': True})
        cls.facility = cls.env['wm.disposal.facility'].create({'name': 'Lock Plant', 'facility_type': 'landfill'})
        cls.category = cls.env['wm.waste.category'].create({'name': 'Lock Waste', 'code': 'LCKW'})
        cls.officer = new_test_user(
            cls.env, login='lock_officer', groups='base.group_user,wm_base.group_wm_admin')

    def _manifest(self, state='draft'):
        manifest = self.env['wm.compliance.manifest'].create({
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
            'transport_mode': 'road',
            'line_ids': [(0, 0, {'waste_category_id': self.category.id, 'quantity': 10.0})],
        })
        if state != 'draft':
            manifest.write({'state': state})
        return manifest

    def test_form_is_read_only_outside_draft(self):
        """Header fields and the waste lines are read-only whenever the state is not draft."""
        arch = self.env['wm.compliance.manifest'].get_view(view_type='form')['arch']
        tree = etree.fromstring(arch)
        for name in self.LOCKED + ('line_ids',):
            nodes = tree.xpath("//sheet//field[@name='%s']" % name)
            self.assertTrue(nodes, "%s is on the form" % name)
            self.assertEqual(nodes[0].get('readonly'), "state != 'draft'",
                             "%s must be locked after submission" % name)
        # The transport mode may still change while the load is on the move
        mode = tree.xpath("//sheet//field[@name='transport_mode']")[0]
        self.assertEqual(mode.get('readonly'), "state == 'disposed'")

    def test_header_locked_for_users_after_submit(self):
        for state in ('submitted', 'collected', 'disposed'):
            manifest = self._manifest(state).with_user(self.officer)
            for field, value in (('generator_id', self.transporter.id),
                                 ('disposal_facility_id', self.facility.id),
                                 ('manifest_date', '2026-01-01')):
                with self.assertRaises(UserError, msg="%s in %s" % (field, state)):
                    manifest.write({field: value})

    def test_transport_mode_stays_editable_until_disposed_in_form_only(self):
        """Deliberate exception: the mode of transport can change after submission."""
        manifest = self._manifest('submitted').with_user(self.officer)
        manifest.write({'transport_mode': 'rail'})
        self.assertEqual(manifest.transport_mode, 'rail')

    def test_lines_locked_for_users_after_submit(self):
        manifest = self._manifest('submitted')
        line = manifest.line_ids.with_user(self.officer)
        with self.assertRaises(UserError):
            line.write({'quantity': 99.0})
        with self.assertRaises(UserError):
            line.unlink()
        with self.assertRaises(UserError):
            self.env['wm.compliance.manifest.line'].with_user(self.officer).create({
                'manifest_id': manifest.id, 'waste_category_id': self.category.id, 'quantity': 1.0})
