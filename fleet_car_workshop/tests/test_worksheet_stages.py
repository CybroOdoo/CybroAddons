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

class TestWorksheetStages(TransactionCase):
    """ TestWorksheetStages tests """

    def test_default_vehicle_ids(self):
        """ Test _default_vehicle_ids function """
        # We need a vehicle detail record for this
        vehicle_model = self.env['fleet.vehicle.model'].create({
            'name': 'Stage Model',
            'brand_id': self.env['fleet.vehicle.model.brand'].create({'name': 'Stage Brand'}).id,
        })
        fleet_vehicle = self.env['fleet.vehicle'].create({
            'model_id': vehicle_model.id,
            'license_plate': 'STAGE-1',
        })
        vehicle_detail = self.env['vehicle.details'].create({
            'vehicle_id': fleet_vehicle.id,
        })
        
        stage = self.env['worksheet.stages'].with_context(default_vehicle_id=vehicle_detail.id).create({
            'name': 'New Stage'
        })
        self.assertIn(vehicle_detail, stage.vehicle_ids)
