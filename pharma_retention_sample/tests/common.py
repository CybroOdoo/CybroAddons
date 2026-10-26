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
from datetime import date

from odoo.addons.pharmaceutical_base.tests.common import PharmaTestCommon


class PharmaRetentionCommon(PharmaTestCommon):
    """A finished product with a retention rule and helpers for released batches."""

    @classmethod
    def setUpClass(cls):
        """Give the product a retention rule and create a retention location."""
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        cls.location = cls.env['stock.location'].create({
            'name': 'Reserve Cabinet',
            'usage': 'internal',
            'location_id': cls.warehouse.view_location_id.id,
            'pharma_is_retention_location': True,
        })
        cls.product_tmpl.write({
            'retention_required': True,
            'retention_period_months': 12,
            'retention_exam_interval_months': 6,
            'retention_container': 'Amber glass bottle',
            'retention_location_id': cls.location.id,
        })

    def released_lot(self, name='RS-LOT-1', expiry=date(2020, 1, 31)):
        """A released batch of the product (expired by default)."""
        lot = self.create_lot(name=name)
        lot.write({'lot_status': 'released', 'expiry_date': expiry})
        return lot

    def draft_sample(self, lot=None, qty=10.0):
        """The operator's draft reserve sample of a released batch."""
        lot = lot or self.released_lot()
        lot.with_user(self.operator).action_create_retention_sample()
        sample = lot.retention_sample_ids
        sample.with_user(self.operator).retained_qty = qty
        return sample

    def retained_sample(self, lot=None, qty=10.0):
        """A confirmed (retained) reserve sample."""
        sample = self.draft_sample(lot, qty)
        sample.with_user(self.operator).action_confirm()
        return sample

    def withdraw(self, sample, qty, purpose='retest', **vals):
        """Record a withdrawal from ``sample`` as the operator."""
        return self.env['pharma.retention.withdrawal'].with_user(self.operator).create(dict({
            'sample_id': sample.id,
            'purpose': purpose,
            'quantity': qty,
            'reason': 'Test withdrawal',
        }, **vals))
