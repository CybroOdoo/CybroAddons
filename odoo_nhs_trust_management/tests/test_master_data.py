# -*- coding: utf-8 -*-
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import NhsTrustCommon


@tagged('post_install', '-at_install')
class TestMasterData(NhsTrustCommon):
    """Region / ICB / ICS / Health Board constraints, computes and copy()."""

    # ------------------------------------------------------------------ #
    #  Region
    # ------------------------------------------------------------------ #
    def test_region_trust_count_read_group(self):
        """nhs.region.trust_count is computed via _read_group and reflects
        the number of trusts attached to that region."""
        self.assertEqual(self.region_ney.trust_count, 1)  # trust_en
        self._make_england_trust(name='Second NEY', ods_code='RNE2')
        self.region_ney.invalidate_recordset(['trust_count'])
        self.assertEqual(self.region_ney.trust_count, 2)

    def test_region_copy_unique_code(self):
        """Copying a region produces a unique code and a '(copy)' name."""
        clone = self.region_ney.copy()
        self.assertNotEqual(clone.code, self.region_ney.code)
        self.assertIn('copy', clone.name.lower())

    # ------------------------------------------------------------------ #
    #  ICB
    # ------------------------------------------------------------------ #
    def test_icb_must_belong_to_england_region(self):
        """_check_region_system rejects an ICB whose region is not England."""
        with self.assertRaises(ValidationError):
            self.env['nhs.icb'].create({
                'name': 'Bad ICB',
                'code': 'ZZZ',
                'region_id': self.region_sco_w.id,  # Scotland -> invalid
            })

    def test_icb_trust_count(self):
        """nhs.icb.trust_count counts linked trusts (@api.depends('trust_ids'))."""
        self.assertEqual(self.icb_ne_cumbria.trust_count, 1)

    def test_icb_action_view_trusts(self):
        """action_view_trusts returns a window action domain-filtered to the ICB."""
        action = self.icb_ne_cumbria.action_view_trusts()
        self.assertEqual(action['res_model'], 'nhs.trust')
        self.assertIn(('icb_id', '=', self.icb_ne_cumbria.id), action['domain'])

    # ------------------------------------------------------------------ #
    #  ICS
    # ------------------------------------------------------------------ #
    def test_ics_region_is_related_stored(self):
        """nhs.ics.region_id is related+stored from its parent ICB."""
        ics = self.env['nhs.ics'].create({
            'name': 'Test ICS',
            'code': 'TICS',
            'icb_id': self.icb_ne_cumbria.id,
        })
        self.assertEqual(ics.region_id, self.icb_ne_cumbria.region_id)

    def test_ics_cascade_delete_with_icb(self):
        """ondelete='cascade' removes the ICS when its ICB is deleted."""
        icb = self.env['nhs.icb'].create({
            'name': 'Disposable ICB', 'code': 'DISP',
            'region_id': self.region_ney.id,
        })
        ics = self.env['nhs.ics'].create({
            'name': 'Child ICS', 'code': 'CICS', 'icb_id': icb.id,
        })
        icb.unlink()
        self.assertFalse(ics.exists())

    # ------------------------------------------------------------------ #
    #  Health Board
    # ------------------------------------------------------------------ #
    def test_health_board_must_belong_to_scotland_region(self):
        """_check_region_system rejects a board placed in an England region."""
        with self.assertRaises(ValidationError):
            self.env['nhs.health.board'].create({
                'name': 'Bad Board',
                'code': 'S0BAD',
                'board_type': 'territorial',
                'region_id': self.region_ney.id,  # England -> invalid
            })

    def test_trust_type_copy_unique_code(self):
        """Copying a trust type produces a unique code."""
        clone = self.type_acute.copy()
        self.assertNotEqual(clone.code, self.type_acute.code)
