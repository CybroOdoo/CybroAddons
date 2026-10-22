# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import json

from odoo.tests import HttpCase, tagged

from .common import VibeCommon

@tagged("post_install", "-at_install")
class TestControllers(VibeCommon, HttpCase):

    def setUp(self):
        super().setUp()
        self.conv = self._make_conversation(user=self.user_a)
        self.module = self._make_module(self.conv)

    def test_download_module(self):
        self.authenticate("vibe_user_a", "vibe_pass_123456")
        res = self.url_open("/vibe/module/%d/download" % self.module.id)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["Content-Type"], "application/zip")
        self.env.invalidate_all()
        self.assertEqual(self.module.download_count, 1)

    def test_download_foreign_module_is_denied(self):
        self.authenticate("vibe_user_b", "vibe_pass_123456")
        res = self.url_open("/vibe/module/%d/download" % self.module.id)
        self.assertIn(res.status_code, (403, 404))
        self.env.invalidate_all()
        self.assertEqual(self.module.download_count, 0)

    def test_export_conversation(self):
        self.authenticate("vibe_user_a", "vibe_pass_123456")
        res = self.url_open("/vibe/conversation/%d/export" % self.conv.id)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.content)
        self.assertEqual(data["exported_from"]["odoo_version"], "20.0")
