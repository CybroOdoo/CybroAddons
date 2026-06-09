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
from odoo.tests import TransactionCase
from psycopg2 import IntegrityError
from odoo.tools import mute_logger

class TestWorksheetTag(TransactionCase):
    """ TestWorksheetTag tests """

    def test_unique_tag_name(self):
        """ Test the unique constraint on worksheet.tag name """
        self.env['worksheet.tag'].create({'name': 'Unique Tag'})
        
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            self.env['worksheet.tag'].create({'name': 'Unique Tag'})
            # Force the cursor to execute the query to trigger the DB constraint
            self.env.cr.flush()
