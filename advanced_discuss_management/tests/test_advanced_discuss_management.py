# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
###############################################################################
from odoo.modules.module import get_manifest
from odoo.tests import TransactionCase, tagged
from odoo.tools import file_path


@tagged('post_install', '-at_install')
class TestAdvancedDiscussManagement(TransactionCase):
    """Check the wiring of the module and the Discuss data its sidebar
    patches rely on."""

    MODULE = 'advanced_discuss_management'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.channel = cls.env['discuss.channel']._create_channel(
            name='Test General', group_id=None)

    def _manifest_assets(self):
        return get_manifest(self.MODULE)['assets']['web.assets_backend']

    def test_01_asset_files_exist(self):
        """Every file declared in the backend assets is shipped with the
        module."""
        for asset in self._manifest_assets():
            self.assertTrue(file_path(asset), f'Missing asset file: {asset}')

    def test_02_assets_in_backend_bundle(self):
        """The kanban board, the sidebar patches and their templates are
        loaded in the backend bundle."""
        bundle_paths = {
            path for path, *_rest in self.env['ir.asset']._get_asset_paths(
                'web.assets_backend', {})
        }
        for asset in self._manifest_assets():
            self.assertIn(f'/{asset}', bundle_paths,
                          f'{asset} is not in web.assets_backend')

    def test_03_thread_has_no_meeting_start(self):
        """A thread of a channel has no meeting start: the sidebar must not
        print an "@ <time>" label for it."""
        thread = self.channel._create_sub_channel(name='Test Thread')
        self.assertEqual(thread.parent_channel_id, self.channel)
        self.assertFalse(thread.meeting_start_dt)

    def test_04_meeting_start_is_creation_time(self):
        """A meeting started now starts when its channel is created, which is
        also the time shown on the right of its sidebar row."""
        meeting = self.env['discuss.channel']._create_group(
            users_to=self.env.user,
            default_display_mode='video_full_screen',
            name='Test Meeting')
        self.assertEqual(meeting.meeting_start_dt, meeting.create_date)
        self.assertIn(
            meeting,
            self.env['discuss.channel'].search(
                meeting._get_meeting_today_domain()),
            'A meeting started now is listed under the "Today" filter.')
