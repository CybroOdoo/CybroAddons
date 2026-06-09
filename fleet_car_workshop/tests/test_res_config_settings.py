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

class TestResConfigSettings(TransactionCase):
    """ TestResConfigSettings tests """

    def test_config_settings(self):
        """ Test res.config.settings for fleet_car_workshop """
        # Try to find an existing sale journal first
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if not journal:
            journal_vals = {
                'name': 'Workshop Journal',
                'type': 'sale',
                'code': 'WSJ',
            }
            # Handle potential nacha_entry_class_code field from other modules
            if 'nacha_entry_class_code' in self.env['account.journal']._fields:
                journal_vals['nacha_entry_class_code'] = 'PPD'
            journal = self.env['account.journal'].create(journal_vals)
        
        config = self.env['res.config.settings'].create({
            'invoice_journal_id': journal.id,
        })
        config.execute()
        
        param = self.env['ir.config_parameter'].sudo().get_param('fleet_car_workshop.invoice_journal_type')
        self.assertEqual(int(param), journal.id)
