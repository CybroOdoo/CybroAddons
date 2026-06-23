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
from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import OdsSyncCommon


@tagged('post_install', '-at_install')
class TestWizards(OdsSyncCommon):
    """Cover the sync-run wizard validation and the conflict resolution flow
    (both the conflict model actions and the bulk resolve wizard)."""

    def _make_pending_conflict(self, field_name='phone', ods_value='NEW'):
        """Build a full run→detail→conflict chain for a phone diff."""
        trust = self.make_england_trust('WZ1', phone='OLD')
        ods_org = self.make_ods_org('WZ1')
        run = self.make_run('full')
        detail = self.Detail.create({
            'sync_run_id': run.id, 'ods_code': 'WZ1', 'outcome': 'conflict',
            'trust_id': trust.id, 'ods_organisation_id': ods_org.id,
        })
        conflict = self.Conflict.create({
            'sync_run_id': run.id, 'sync_detail_id': detail.id, 'trust_id': trust.id,
            'ods_organisation_id': ods_org.id, 'field_name': field_name,
            'current_value': 'OLD', 'ods_value': ods_value, 'state': 'pending',
        })
        return trust, conflict

    # ---- sync run wizard ---------------------------------------------
    def test_run_wizard_requires_role_for_specific_role(self):
        """'Specific Role' scope without a role mapping is rejected."""
        wiz = self.env['nhs.ods.sync.run.wizard'].create(
            {'mode': 'live', 'scope': 'specific_role'})
        with self.assertRaises(UserError):
            wiz.action_confirm()

    def test_run_wizard_requires_code_for_specific_org(self):
        """'Specific Organisation' scope without an ODS code is rejected."""
        wiz = self.env['nhs.ods.sync.run.wizard'].create(
            {'mode': 'live', 'scope': 'specific_org'})
        with self.assertRaises(UserError):
            wiz.action_confirm()

    # ---- conflict model actions --------------------------------------
    def test_conflict_use_ods_writes_value(self):
        """action_use_ods writes the ODS value onto the trust and resolves."""
        trust, conflict = self._make_pending_conflict()
        conflict.action_use_ods()
        self.assertEqual(conflict.state, 'resolved_use_ods')
        self.assertEqual(trust.phone, 'NEW')

    def test_conflict_keep_local_keeps_value(self):
        """action_keep_local resolves without touching the trust value."""
        trust, conflict = self._make_pending_conflict()
        conflict.action_keep_local()
        self.assertEqual(conflict.state, 'resolved_keep_local')
        self.assertEqual(trust.phone, 'OLD')

    def test_conflict_ignore_requires_note(self):
        """action_ignore demands a resolution note before suppressing the conflict."""
        trust, conflict = self._make_pending_conflict()
        with self.assertRaises(UserError):
            conflict.action_ignore()

    # ---- bulk resolve wizard -----------------------------------------
    def test_resolve_wizard_accept_ods(self):
        """The bulk wizard with 'Accept ODS' applies the ODS value."""
        trust, conflict = self._make_pending_conflict()
        wiz = self.env['nhs.ods.conflict.resolve.wizard'].create({
            'conflict_ids': [(6, 0, [conflict.id])],
            'resolution': 'accept_ods',
        })
        wiz.action_confirm()
        self.assertEqual(conflict.state, 'resolved_use_ods')
        self.assertEqual(trust.phone, 'NEW')

    def test_resolve_wizard_ignore_requires_reason(self):
        """The bulk wizard rejects 'Ignore' with no reason supplied."""
        trust, conflict = self._make_pending_conflict()
        wiz = self.env['nhs.ods.conflict.resolve.wizard'].create({
            'conflict_ids': [(6, 0, [conflict.id])],
            'resolution': 'ignore',
        })
        with self.assertRaises(UserError):
            wiz.action_confirm()
