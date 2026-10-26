# -*- coding: utf-8 -*-
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
from odoo import fields

from odoo.addons.pharmaceutical_base.tests.test_manufacturing import PharmaManufacturingCommon


class EquipmentCommon(PharmaManufacturingCommon):
    """Equipment categories, a QA-only reviewer and helpers to make equipment fit."""

    @classmethod
    def setUpClass(cls):
        """Create the categories and the QA-only reviewer."""
        super().setUpClass()
        ref = cls.env.ref
        cls.Equipment = cls.env['maintenance.equipment']
        cls.Request = cls.env['maintenance.request']
        cls.Calibration = cls.env['pharma.calibration.result']
        cls.qa_only = cls.env['res.users'].create({
            'name': 'QA Only', 'login': 'pharma_equipment_qa_only',
            'group_ids': [(4, ref('pharmaceutical_base.group_pharma_role_qa').id),
                          (4, ref('stock.group_stock_user').id),
                          (4, ref('mrp.group_mrp_user').id)],
        })
        Category = cls.env['maintenance.equipment.category']
        cls.cat_testing = Category.create({'name': 'Balances', 'equipment_class': 'testing'})
        cls.cat_mfg = Category.create({
            'name': 'Granulators', 'equipment_class': 'manufacturing', 'gmp_critical': True})
        cls.cat_utility = Category.create({'name': 'HVAC', 'equipment_class': 'utility'})

    def instrument(self, name='Balance AB-220', **vals):
        """A testing instrument that needs calibration."""
        return self.Equipment.create(dict({
            'name': name, 'category_id': self.cat_testing.id, 'calibration_required': True,
        }, **vals))

    def machine(self, name='Granulator HSG-200', **vals):
        """GMP critical manufacturing equipment at the order's work centre."""
        return self.Equipment.create(dict({
            'name': name, 'category_id': self.cat_mfg.id,
            'workcenter_ids': [(6, 0, self.workcenter.ids)],
        }, **vals))

    def calibration(self, equipment, as_found=100.1, as_left=100.0, **vals):
        """A calibration in progress with one 100 g check point (tolerance 0.5)."""
        result = self.Calibration.with_user(self.operator).create(dict({
            'equipment_id': equipment.id,
            'certificate_number': 'CERT-1',
            'point_ids': [(0, 0, {'nominal_value': 100.0, 'as_found': as_found,
                                  'as_left': as_left, 'tolerance': 0.5, 'unit': 'g'})],
        }, **vals))
        result.action_start()
        return result

    def calibrate(self, equipment, **kwargs):
        """Calibrate ``equipment`` and have QA verify it."""
        result = self.calibration(equipment, **kwargs)
        result.action_complete()
        result.with_user(self.qa_only).action_qa_verify()
        return result

    def request(self, equipment, maintenance_type='cleaning', **vals):
        """A new request of ``maintenance_type`` raised by the operator."""
        return self.Request.with_user(self.operator).create(dict({
            'name': 'Work on %s' % equipment.name,
            'equipment_id': equipment.id,
            'maintenance_type': maintenance_type,
        }, **vals))

    def complete(self, request, verify=True):
        """Start and complete ``request``, then QA verifies it unless told otherwise."""
        request = request.with_user(self.operator)
        request.action_pharma_start()
        request.work_done = 'Done as per SOP.'
        request.action_pharma_complete()
        if verify:
            request.with_user(self.qa_only).action_qa_verify()
        return request

    def clean(self, equipment, **vals):
        """Clean ``equipment`` through a QA-verified cleaning request."""
        return self.complete(self.request(equipment, 'cleaning', **vals))

    def fit_instrument(self, **vals):
        """A calibrated, clean instrument."""
        instrument = self.instrument(**vals)
        self.calibrate(instrument)
        self.clean(instrument)
        return instrument

    def set_check(self, mode):
        """Set the site's equipment check (off, warn or block)."""
        self.env['ir.config_parameter'].sudo().set_param('pharma_equipment.check', mode)

    def enable_sterile(self):
        """Switch sterile manufacturing on for the site."""
        self.env['res.config.settings'].create({'group_pharma_sterile_mfg': True}).execute()

    @staticmethod
    def days(n):
        """Today plus ``n`` days."""
        return fields.Date.add(fields.Date.today(), days=n)
