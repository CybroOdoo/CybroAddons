# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
import os
import tempfile
from unittest.mock import MagicMock, patch

from odoo.tests.common import BaseCase, tagged

from odoo.addons.restrict_logins.utils import (
    clear_all_session_files, clear_session_history)

ROOT = 'odoo.addons.restrict_logins.utils.root'


@tagged('post_install', '-at_install')
class TestSessionFiles(BaseCase):
    """Tests of the session file helpers."""

    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = tmp.name
        self.store = MagicMock()
        self.store.path = self.path
        self.store.get_session_filename.side_effect = (
            lambda sid: os.path.join(self.path, sid[:2], sid))

    def _create_session(self, sid):
        directory = os.path.join(self.path, sid[:2])
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, sid)
        with open(path, 'w', encoding='utf-8') as session_file:
            session_file.write('session')
        return path

    def test_clear_session_history_deletes_file(self):
        path = self._create_session('ab-session')
        with patch(ROOT) as root:
            root.session_store = self.store
            self.assertTrue(clear_session_history('ab-session'))
        self.assertFalse(os.path.exists(path))

    def test_clear_session_history_missing_file(self):
        with patch(ROOT) as root:
            root.session_store = self.store
            self.assertTrue(clear_session_history('zz-missing'))

    def test_clear_session_history_without_sid(self):
        self.assertTrue(clear_session_history(False))

    def test_clear_session_history_invalid_sid(self):
        self.store.get_session_filename.side_effect = ValueError('invalid')
        with patch(ROOT) as root:
            root.session_store = self.store
            self.assertTrue(clear_session_history('bad'))

    def test_clear_session_history_os_error(self):
        self._create_session('ab-session')
        with patch(ROOT) as root, patch(
                'os.remove', side_effect=PermissionError('denied')):
            root.session_store = self.store
            self.assertFalse(clear_session_history('ab-session'))

    def test_clear_all_session_files(self):
        paths = [self._create_session(sid)
                 for sid in ('aa-one', 'aa-two', 'bb-three')]
        with patch(ROOT) as root:
            root.session_store = self.store
            self.assertEqual(clear_all_session_files(), 3)
        self.assertFalse(any(os.path.exists(path) for path in paths))

    def test_clear_all_session_files_ignores_errors(self):
        self._create_session('aa-one')
        with patch(ROOT) as root, patch(
                'os.unlink', side_effect=OSError('busy')):
            root.session_store = self.store
            self.assertEqual(clear_all_session_files(), 0)
