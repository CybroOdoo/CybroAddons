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
from datetime import datetime, timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestScheduledDatesValidation(TransactionCase):
    """Unit tests verifying collection schedule date ranges and validation constraints."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Date Validation Customer'})
        cls.collection_point = cls.env['wm.collection.point'].create({
            'name': 'Validation Point',
            'partner_id': cls.partner.id,
        })
        cls.now = datetime.now()

    def test_valid_scheduled_dates(self):
        """
        Valid scheduled_start < scheduled_end should create cleanly.
        """
        order = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.collection_point.id,
            'scheduled_start': self.now,
            'scheduled_end': self.now + timedelta(hours=2),
        })
        self.assertTrue(order.id)

    def test_invalid_scheduled_end_before_start(self):
        """
        scheduled_end before scheduled_start must raise ValidationError.
        """
        with self.assertRaises(ValidationError):
            self.env['wm.collection.order'].create({
                'partner_id': self.partner.id,
                'collection_point_id': self.collection_point.id,
                'scheduled_start': self.now,
                'scheduled_end': self.now - timedelta(hours=1),
            })

    def test_invalid_scheduled_end_equal_start(self):
        """
        scheduled_end equal to scheduled_start must raise ValidationError.
        """
        with self.assertRaises(ValidationError):
            self.env['wm.collection.order'].create({
                'partner_id': self.partner.id,
                'collection_point_id': self.collection_point.id,
                'scheduled_start': self.now,
                'scheduled_end': self.now,
            })

    def test_invalid_actual_end_before_start(self):
        """
        actual_end before actual_start must raise ValidationError.
        """
        with self.assertRaises(ValidationError):
            self.env['wm.collection.order'].create({
                'partner_id': self.partner.id,
                'collection_point_id': self.collection_point.id,
                'actual_start': self.now,
                'actual_end': self.now - timedelta(minutes=30),
            })
