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
from odoo import api, fields, models


class StockLot(models.Model):
    """Adds backward/forward batch genealogy relations to stock.lot."""

    _inherit = 'stock.lot'

    produced_production_ids = fields.Many2many(
        'mrp.production',
        compute='_compute_genealogy',
        string='Production Orders',
        help='Manufacturing orders that produced this lot.',
    )
    consumed_lot_ids = fields.Many2many(
        'stock.lot',
        compute='_compute_genealogy',
        string='Raw Material Lots',
        help='Raw-material lots used to produce this lot.',
    )
    vendor_ids = fields.Many2many(
        'res.partner',
        compute='_compute_genealogy',
        string='Vendors',
        help='Vendors who supplied this lot or its raw-material lots.',
    )
    purchase_order_ids = fields.Many2many(
        'purchase.order',
        compute='_compute_genealogy',
        string='Purchase Orders',
        help='Purchase orders through which this lot or its raw-material lots were received.',
    )
    delivery_order_ids = fields.Many2many(
        'stock.picking',
        compute='_compute_genealogy',
        string='Delivery Orders',
        help='Delivery orders that shipped this lot.',
    )
    customer_ids = fields.Many2many(
        'res.partner',
        compute='_compute_genealogy',
        string='Customers',
        help='Customers who received this lot.',
    )
    invoice_ids = fields.Many2many(
        'account.move',
        compute='_compute_genealogy',
        string='Customer Invoices',
        help='Customer invoices of the sales that shipped this lot.',
    )
    qc_test_ids = fields.Many2many(
        'pharma.qc.test.order',
        compute='_compute_genealogy',
        string='QC Test Orders',
        help='QC test orders of this lot and its raw-material lots.',
    )
    incoming_qc_ids = fields.Many2many(
        'pharma.qc.test.order',
        help='Incoming QC test orders of this lot and its raw-material lots.',
        compute='_compute_genealogy_qc',
        string='Incoming QC',
    )
    ipqc_ids = fields.Many2many(
        'pharma.qc.test.order',
        help='In-process QC test orders of this lot and its raw-material lots.',
        compute='_compute_genealogy_qc',
        string='IPQC',
    )
    fg_qc_ids = fields.Many2many(
        'pharma.qc.test.order',
        help='Finished-goods QC test orders of this lot.',
        compute='_compute_genealogy_qc',
        string='FG QC',
    )
    bmr_ids = fields.Many2many(
        'pharma.bmr',
        compute='_compute_genealogy',
        string='BMRs',
        help='Batch manufacturing records of the orders that produced this lot.',
    )
    deviation_ids = fields.Many2many(
        comodel_name='pharma.deviation',
        help='Deviations raised on this lot, its batch or its raw-material lots.',
        compute='_compute_deviation_capa',
        string='Deviations',
    )
    capa_ids = fields.Many2many(
        comodel_name='pharma.capa',
        help='CAPAs raised from the deviations of this lot, its batch or its raw-material lots.',
        compute='_compute_deviation_capa',
        string='CAPAs',
    )
    deviation_count = fields.Integer(
        help='Number of deviations linked to this lot, its batch or its raw-material lots.',
        compute='_compute_deviation_capa',
    )
    capa_count = fields.Integer(
        string='CAPA Count',
        help='Number of CAPAs linked to this lot, its batch or its raw-material lots.',
        compute='_compute_deviation_capa',
    )
    oos_investigation_ids = fields.Many2many(
        'pharma.oos.investigation',
        compute='_compute_genealogy',
        string='OOS Investigations',
        help='OOS investigations raised on the QC results of this lot and its raw-material lots.',
    )
    coa_ids = fields.Many2many(
        'pharma.coa',
        compute='_compute_genealogy',
        string='Certificates of Analysis',
        help='Certificates of Analysis issued for this lot.',
    )

    def _compute_genealogy(self):
        """Compile the full backward and forward traceability data for this lot."""
        for lot in self:
            # The MO link on a finished-goods move line is not always on the
            # line's own production_id, so match move_id.production_id too.
            produced_sml = self.env['stock.move.line'].search(
                [
                    ('lot_id', '=', lot.id),
                    '|',
                    ('production_id', '!=', False),
                    ('move_id.production_id', '!=', False),
                ]
            )
            productions = produced_sml.mapped('production_id') | produced_sml.mapped('move_id.production_id')
            lot.produced_production_ids = productions

            # Consumption is not always recorded on the raw moves, so fall back
            # to the received lots of the BOM components.
            if productions:
                consumed_lots = self.env['stock.lot']
                for prod in productions:
                    consumed_lots |= prod._pharma_raw_material_lots()
                consumed_lots -= lot
            else:
                consumed_lots = self.env['stock.lot']
            lot.consumed_lot_ids = consumed_lots

            all_lots = lot + consumed_lots
            # Purchases and invoices are only linked for users who may read
            # them; the genealogy is opened by every pharma role.
            if all_lots and self.env['purchase.order'].has_access('read'):
                incoming_sml = self.env['stock.move.line'].search(
                    [
                        ('lot_id', 'in', all_lots.ids),
                        ('picking_id.picking_type_id.code', '=', 'incoming'),
                        ('state', '=', 'done'),
                    ]
                )
                purchases = incoming_sml.mapped('move_id.purchase_line_id.order_id')
                vendors = purchases.mapped('partner_id')
            else:
                purchases = self.env['purchase.order']
                vendors = self.env['res.partner']
            # Written as superuser so an empty value needs no read right on the
            # comodel; only records the user may read are ever linked.
            lot.sudo().purchase_order_ids = purchases
            lot.vendor_ids = vendors
            outgoing_sml = self.env['stock.move.line'].search(
                [
                    ('lot_id', '=', lot.id),
                    ('picking_id.picking_type_id.code', '=', 'outgoing'),
                    ('state', '=', 'done'),
                ]
            )
            deliveries = outgoing_sml.mapped('picking_id')
            lot.delivery_order_ids = deliveries

            lot.customer_ids = deliveries.mapped('partner_id')

            if hasattr(deliveries, 'sale_id') and self.env['account.move'].has_access('read'):
                sales = deliveries.mapped('sale_id')
                invoices = sales.mapped('invoice_ids')
            else:
                invoices = self.env['account.move']
            lot.sudo().invoice_ids = invoices
            # QC and OOS span the finished lot and its consumed raw-material lots.
            quality_lots = lot + consumed_lots
            lot.qc_test_ids = self.env['pharma.qc.test.order'].search([('lot_id', 'in', quality_lots.ids)])
            lot.oos_investigation_ids = self.env['pharma.oos.investigation'].search(
                [('result_line_id.test_order_id.lot_id', 'in', quality_lots.ids)]
            )
            # CoAs are issued per finished lot only (raw materials have no CoA).
            lot.coa_ids = self.env['pharma.coa'].search([('lot_id', '=', lot.id)])
            lot.bmr_ids = self.env['pharma.bmr'].search([('production_id', 'in', productions.ids)])

    @api.depends('bmr_ids', 'consumed_lot_ids')
    def _compute_deviation_capa(self):
        """Deviations and CAPAs for this lot and its consumed raw-material lots."""
        for lot in self:
            productions = lot.bmr_ids.mapped('production_id')
            quality_lots = lot | lot.consumed_lot_ids
            devs = self.env['pharma.deviation'].search(
                ['|', ('batch_id', 'in', productions.ids), ('lot_id', 'in', quality_lots.ids)]
            )
            capas = (
                self.env['pharma.capa'].search([('deviation_id', 'in', devs.ids)])
                if devs
                else self.env['pharma.capa']
            )
            lot.deviation_ids = devs.ids
            lot.capa_ids = capas.ids
            lot.deviation_count = len(devs)
            lot.capa_count = len(capas)

    def action_view_lot_deviations(self):
        """Open the deviations linked to this lot."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Deviations'),
            'res_model': 'pharma.deviation',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.deviation_ids.ids)],
        }

    def action_view_lot_capas(self):
        """Open the CAPAs linked to this lot."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('CAPAs'),
            'res_model': 'pharma.capa',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.capa_ids.ids)],
        }

    def _compute_genealogy_qc(self):
        """Splits QC tests into categories based on stage for genealogy view."""
        for lot in self:
            # Stage values come from pharma.qc.test.order: 'incoming' (raw
            # material), 'ipqc' (in-process) and 'finished' (FG).
            lot.incoming_qc_ids = lot.qc_test_ids.filtered(lambda q: q.stage == 'incoming')
            lot.ipqc_ids = lot.qc_test_ids.filtered(lambda q: q.stage == 'ipqc')
            lot.fg_qc_ids = lot.qc_test_ids.filtered(lambda q: q.stage == 'finished')
