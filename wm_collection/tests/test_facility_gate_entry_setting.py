#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestFacilityGateEntrySetting(TransactionCase):
    """Unit tests verifying facility gate entry configuration setting toggle."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.facility = cls.env['wm.disposal.facility'].create({'name': 'Test Disposal Facility'})
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Gate Brand'})
        model = cls.env['fleet.vehicle.model'].create({'name': 'Gate Model', 'brand_id': brand.id})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': model.id,
            'license_plate': 'GATE-TEST-01',
        })

    def test_facility_gate_entry_setting_toggle(self):
        """Test enabling and disabling Facility Gate Entries via res.config.settings."""
        # Enable setting via res.config.settings
        settings = self.env['res.config.settings'].create({'use_facility_gate_entry': True})
        settings.execute()

        val = self.env['ir.config_parameter'].sudo().get_param('wm_collection.use_facility_gate_entry')
        self.assertEqual(val, 'True', "Config parameter must be 'True' when setting is enabled.")

        menu = self.env.ref('wm_collection.menu_wm_facility_gate_entry', raise_if_not_found=False)
        if menu:
            self.assertTrue(menu.active, "Menu item must be active when setting is enabled.")

        # Creation should succeed when enabled
        entry = self.env['wm.facility.gate.entry'].create({
            'facility_id': self.facility.id,
            'vehicle_id': self.vehicle.id,
            'confirmed_weight': 2000.0,
        })
        self.assertTrue(entry.id, "Gate entry creation should succeed when setting is enabled.")

        # Disable setting via res.config.settings
        settings = self.env['res.config.settings'].create({'use_facility_gate_entry': False})
        settings.execute()

        val = self.env['ir.config_parameter'].sudo().get_param('wm_collection.use_facility_gate_entry')
        self.assertEqual(val, 'False', "Config parameter must be 'False' when setting is disabled.")

        if menu:
            self.assertFalse(menu.active, "Menu item must be deactivated when setting is disabled.")

        # Creating gate entry when disabled should raise UserError
        with self.assertRaises(UserError):
            self.env['wm.facility.gate.entry'].create({
                'facility_id': self.facility.id,
                'vehicle_id': self.vehicle.id,
                'confirmed_weight': 2000.0,
            })
