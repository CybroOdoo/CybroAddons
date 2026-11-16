# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'theme_eco_refine')
class TestWebsiteSelect(TransactionCase):
    """Tests for the `select` field added on website."""

    def test_select_defaults_to_false(self):
        website = self.env['website'].create({'name': 'Test Website'})
        self.assertFalse(website.select)

    def test_select_can_be_toggled(self):
        website = self.env['website'].create({'name': 'Test Website'})
        website.select = True
        self.assertTrue(website.select)