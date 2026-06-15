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
from odoo.exceptions import ValidationError, UserError
from odoo.tests import tagged

from .common import NhsTrustCommon


@tagged('post_install', '-at_install')
class TestStateWorkflow(NhsTrustCommon):
    """Workflow guard rails: direct-write block, transition graph, wizard,
    immutable audit log, and the merge / dissolve wizards."""

    # ------------------------------------------------------------------ #
    #  Direct write protection
    # ------------------------------------------------------------------ #
    def test_direct_state_write_blocked(self):
        """Writing `state` without the approved context raises UserError."""
        with self.assertRaises(UserError):
            self.trust_en.write({'state': 'under_review'})

    def test_approved_context_allows_valid_transition(self):
        """The approved context permits a *legal* transition."""
        self.trust_en.with_context(approved_state_change=True).write(
            {'state': 'under_review'})
        self.assertEqual(self.trust_en.state, 'under_review')

    def test_illegal_transition_blocked_even_when_approved(self):
        """Transition legality is enforced before the context check:
        draft -> active is illegal and raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.trust_en.with_context(approved_state_change=True).write(
                {'state': 'active'})

    def test_dissolved_is_terminal(self):
        """No transition is allowed out of 'dissolved'."""
        self._force_state(self.trust_en, 'dissolved')
        with self.assertRaises(ValidationError):
            self.trust_en.with_context(approved_state_change=True).write(
                {'state': 'active'})

    # ------------------------------------------------------------------ #
    #  State-change wizard
    # ------------------------------------------------------------------ #
    def test_wizard_executes_transition_and_logs(self):
        """The wizard writes the new state AND appends one immutable log row."""
        wizard = self.env['nhs.trust.state.change.wizard'].create({
            'trust_id': self.trust_en.id,
            'new_state': 'under_review',
            'reason': 'Initial governance submission for review.',
        })
        wizard.action_confirm()
        self.assertEqual(self.trust_en.state, 'under_review')
        log = self.env['nhs.trust.state.log'].search(
            [('trust_id', '=', self.trust_en.id)])
        self.assertRecordValues(log, [{
            'from_state': 'draft',
            'to_state': 'under_review',
        }])

    def test_wizard_reason_minimum_length(self):
        """A justification under 5 characters is rejected."""
        with self.assertRaises(ValidationError):
            self.env['nhs.trust.state.change.wizard'].create({
                'trust_id': self.trust_en.id,
                'new_state': 'under_review',
                'reason': 'no',
            })

    def test_wizard_rejects_illegal_transition(self):
        """The wizard's own constrains reject an illegal target state."""
        with self.assertRaises(ValidationError):
            self.env['nhs.trust.state.change.wizard'].create({
                'trust_id': self.trust_en.id,
                'new_state': 'dissolved',          # draft -> dissolved illegal
                'reason': 'Trying to skip the workflow.',
            })

    def test_wizard_blocks_scotland_special_measures(self):
        """Scotland trusts cannot be escalated to Special Measures via wizard."""
        self._force_state(self.trust_sco, 'active')
        with self.assertRaises(ValidationError):
            self.env['nhs.trust.state.change.wizard'].create({
                'trust_id': self.trust_sco.id,
                'new_state': 'special_measures',
                'reason': 'Should not be permitted for Scotland.',
            })

    # ------------------------------------------------------------------ #
    #  Immutable audit log
    # ------------------------------------------------------------------ #
    def test_state_log_is_immutable(self):
        """Existing log rows can never be written to."""
        log = self.env['nhs.trust.state.log'].create({
            'trust_id': self.trust_en.id,
            'to_state': 'under_review',
            'reason': 'seed',
        })
        with self.assertRaises(UserError):
            log.write({'reason': 'tampered'})

    def test_state_log_display_name(self):
        """display_name renders 'Trust -> <State Label>'."""
        log = self.env['nhs.trust.state.log'].create({
            'trust_id': self.trust_en.id,
            'to_state': 'active',
            'reason': 'seed',
        })
        self.assertIn('Active', log.display_name)
        self.assertIn(self.trust_en.name, log.display_name)

    # ------------------------------------------------------------------ #
    #  Dissolve wizard
    # ------------------------------------------------------------------ #
    def test_dissolve_wizard(self):
        """Dissolving an active trust sets state=dissolved, detaches board
        members and logs the event."""
        self._force_state(self.trust_en, 'active')
        self.env['res.partner'].create({
            'name': 'Board Member To Detach',
            'is_nhs_board_member': True,
            'nhs_trust_id': self.trust_en.id,
            'nhs_board_role': 'non_exec',
        })
        wizard = self.env['nhs.trust.dissolve.wizard'].create({
            'trust_id': self.trust_en.id,
            'reason': 'Legal dissolution order #2026-001.',
        })
        wizard.action_confirm_dissolve()
        self.assertEqual(self.trust_en.state, 'dissolved')
        self.assertEqual(self.trust_en.board_member_count, 0,
                         "Board members must be detached on dissolution.")

    # ------------------------------------------------------------------ #
    #  Merge wizard
    # ------------------------------------------------------------------ #
    def test_merge_wizard_same_region_required(self):
        """The merge target must share the source's region."""
        source = self._make_england_trust(name='Source', ods_code='RSRC')
        self._force_state(source, 'active')
        # Target in a different region (London) - must be active per domain.
        target = self._make_england_trust(
            name='Target', ods_code='RTGT',
            region_id=self.region_ney.id)         # same region -> valid baseline
        self._force_state(target, 'active')

        wizard = self.env['nhs.trust.merge.wizard'].create({
            'source_trust_id': source.id,
            'target_trust_id': target.id,
            'reason': 'Statutory merger order reference 12345.',
            'transfer_board_members': True,
        })
        wizard.action_confirm_merge()
        self.assertEqual(source.state, 'merging')

    def test_merge_wizard_cross_region_rejected(self):
        """A merge across regions is rejected by the constrains."""
        source = self._make_england_trust(name='Src2', ods_code='RSR2')
        target_ldn = self.NhsTrust.create({
            'name': 'Ldn Target', 'ods_code': 'RLDN',
            'health_system': 'nhs_england',
            'trust_type_id': self.type_acute.id,
            'region_id': self.region_ldn.id,
            'icb_id': self.env.ref(
                'odoo_nhs_trust_management.icb_north_central_london').id,
        })
        with self.assertRaises(ValidationError):
            self.env['nhs.trust.merge.wizard'].create({
                'source_trust_id': source.id,
                'target_trust_id': target_ldn.id,
                'reason': 'Cross-region merge should fail.',
            })
