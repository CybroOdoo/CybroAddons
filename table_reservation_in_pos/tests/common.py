# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import Command
from odoo.tests.common import TransactionCase


class TableReservationCommon(TransactionCase):
    """Shared fixtures: a restaurant floor with a few tables."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Table = cls.env['restaurant.table']
        cls.config = cls.env['pos.config'].search([], limit=1)
        if not cls.config:
            # Fresh databases without demo data have no POS config.
            cls.config = cls.env['pos.config'].create({
                'name': 'Reservation Test Config',
            })
        floor_vals = {'name': 'Reservation Test Floor'}
        if cls.config and 'pos_config_ids' in cls.env['restaurant.floor']._fields:
            floor_vals['pos_config_ids'] = [Command.link(cls.config.id)]
        cls.floor = cls.env['restaurant.floor'].create(floor_vals)
        cls._counter = 0
        cls.table_1 = cls._make_table()
        cls.table_2 = cls._make_table()
        cls.table_3 = cls._make_table()

    @classmethod
    def _make_table(cls, **vals):
        """Create a table using whichever naming field this version has."""
        cls._counter += 1
        vals.setdefault('floor_id', cls.floor.id)
        if 'table_number' in cls.Table._fields:
            vals.setdefault('table_number', 900 + cls._counter)
        elif 'name' in cls.Table._fields:
            vals.setdefault('name', 'T%s' % (900 + cls._counter))
        return cls.Table.create(vals)
