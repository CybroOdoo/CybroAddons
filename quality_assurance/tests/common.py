# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies
#    (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import Command
from odoo.tests import TransactionCase


class QualityCommon(TransactionCase):
    """Shared fixtures for the quality_assurance test-suite."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        cls.in_type = cls.warehouse.in_type_id
        cls.out_type = cls.warehouse.out_type_id
        cls.partner = cls.env['res.partner'].create({'name': 'QA Vendor'})

        # Product with quality measures configured.
        cls.product = cls.env['product.product'].create({
            'name': 'QA Product',
            'type': 'consu',
        })
        # Product without any quality measure.
        cls.product_plain = cls.env['product.product'].create({
            'name': 'QA Plain Product',
            'type': 'consu',
        })
        cls.measure_qty = cls.env['quality.measure'].create({
            'name': 'Weight Check',
            'product_id': cls.product.id,
            'type': 'quantity',
            'quantity_min': 5.0,
            'quantity_max': 10.0,
            'picking_type_ids': [Command.set(cls.in_type.ids)],
        })
        cls.measure_ql = cls.env['quality.measure'].create({
            'name': 'Visual Check',
            'product_id': cls.product.id,
            'type': 'quality',
            'picking_type_ids': [Command.set(cls.in_type.ids)],
        })

    @classmethod
    def _create_picking(cls, products=None, picking_type=None, qty=5.0):
        """Create a draft picking with one move per product."""
        products = products or cls.product
        picking_type = picking_type or cls.in_type
        src = picking_type.default_location_src_id
        dest = picking_type.default_location_dest_id
        move_fields = cls.env['stock.move']._fields
        # The UoM field name differs between Odoo versions.
        uom_fname = next(
            (fname for fname in ('product_uom_id', 'product_uom')
             if fname in move_fields), None)
        move_vals = []
        for product in products:
            vals = {
                'product_id': product.id,
                'product_uom_qty': qty,
                'location_id': src.id,
                'location_dest_id': dest.id,
            }
            if uom_fname:
                vals[uom_fname] = product.uom_id.id
            if 'name' in move_fields:
                vals['name'] = product.name
            move_vals.append(Command.create(vals))
        return cls.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'partner_id': cls.partner.id,
            'location_id': src.id,
            'location_dest_id': dest.id,
            'move_ids': move_vals,
        })

    @classmethod
    def _get_alerts(cls, picking):
        return cls.env['quality.alert'].search(
            [('picking_id', '=', picking.id)])

    @classmethod
    def _make_ready(cls, picking):
        """Confirm, reserve and mark every move as picked."""
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
            move.picked = True

    @classmethod
    def _fill_tests(cls, alert, qty_result=7.0, ql_result='satisfied'):
        """Fill in results for every test of the alert."""
        for test in alert.tests:
            if test.test_type == 'quantity':
                test.test_result = qty_result
            else:
                test.test_result2 = ql_result
