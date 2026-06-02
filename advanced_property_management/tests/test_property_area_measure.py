# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestPropertyAreaMeasure(TransactionCase):

    def test_compute_area_uses_length_and_width(self):
        measure = self.env["property.area.measure"].create({
            "name": "Living Room",
            "length": 12.0,
            "width": 10.0,
            "height": 8.0,
        })

        self.assertEqual(measure.area, 120.0)
