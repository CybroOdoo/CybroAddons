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
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'wm_compliance')
class TestComplianceDecisions(TransactionCase):
    """Decision 9: an empty manifest can never be disposed / certified."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.generator = cls.env['res.partner'].create({'name': 'Dec Generator', 'is_generator': True})
        cls.transporter = cls.env['res.partner'].create({'name': 'Dec Transporter', 'is_transporter': True})
        cls.facility = cls.env['wm.disposal.facility'].create({'name': 'Dec Plant', 'facility_type': 'landfill'})
        cls.category = cls.env['wm.waste.category'].create({'name': 'Dec Waste', 'code': 'DECW'})

    def _collected_manifest(self, quantity):
        manifest = self.env['wm.compliance.manifest'].create({
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
            'line_ids': [(0, 0, {'waste_category_id': self.category.id, 'quantity': quantity})],
        })
        manifest.action_submit()
        manifest.action_collect()
        self.assertEqual(manifest.state, 'collected')
        return manifest

    def _assert_not_disposed(self, manifest):
        with self.assertRaisesRegex(UserError, 'empty manifest'):
            manifest.action_dispose()
        self.assertEqual(manifest.state, 'collected')
        self.assertFalse(self.env['wm.compliance.certificate'].search(
            [('manifest_id', '=', manifest.id)]))

    def test_zero_quantity_manifest_cannot_be_disposed(self):
        self._assert_not_disposed(self._collected_manifest(0.0))

    def test_manifest_without_lines_cannot_be_disposed(self):
        manifest = self._collected_manifest(10.0)
        # Superuser bypasses the submitted-manifest line lock
        manifest.line_ids.sudo().unlink()
        self.assertFalse(manifest.line_ids)
        self.assertEqual(manifest.total_quantity, 0.0)
        self._assert_not_disposed(manifest)

    def test_manifest_with_quantity_is_disposed_and_certified(self):
        manifest = self._collected_manifest(42.0)
        manifest.action_dispose()
        self.assertEqual(manifest.state, 'disposed')
        cert = self.env['wm.compliance.certificate'].search([('manifest_id', '=', manifest.id)])
        self.assertTrue(cert)
        self.assertAlmostEqual(cert.quantity, 42.0)
