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

    produced_production_ids = fields.Many2many('mrp.production', compute='_compute_genealogy',
                                               string='Production Orders',
                                               help='Specifies the Production Orders for this record.')
    consumed_lot_ids = fields.Many2many('stock.lot', compute='_compute_genealogy',
                                        string='Raw Material Lots',
                                        help='Specifies the Raw Material Lots for this record.')
    vendor_ids = fields.Many2many('res.partner', compute='_compute_genealogy', string='Vendors',
                                  help='Specifies the Vendors for this record.')
    purchase_order_ids = fields.Many2many('purchase.order', compute='_compute_genealogy',
                                          string='Purchase Orders',
                                          help='Specifies the Purchase Orders for this record.')

    delivery_order_ids = fields.Many2many('stock.picking', compute='_compute_genealogy',
                                          string='Delivery Orders',
                                          help='Specifies the Delivery Orders for this record.')
    customer_ids = fields.Many2many('res.partner', compute='_compute_genealogy',
                                    string='Customers', help='Specifies the Customers for this record.')
    invoice_ids = fields.Many2many('account.move', compute='_compute_genealogy',
                                   string='Customer Invoices', help='Specifies the Customer Invoices for this record.')

    qc_test_ids = fields.Many2many('pharma.qc.test.order', compute='_compute_genealogy',
                                   string='QC Test Orders', help='Specifies the QC Test Orders for this record.')
    incoming_qc_ids = fields.Many2many('pharma.qc.test.order', help='Specifies the Incoming Qc Ids for this record.', compute='_compute_genealogy_qc', string='Incoming QC')
    ipqc_ids = fields.Many2many('pharma.qc.test.order', help='Specifies the Ipqc Ids for this record.', compute='_compute_genealogy_qc', string='IPQC')
    fg_qc_ids = fields.Many2many('pharma.qc.test.order', help='Specifies the Fg Qc Ids for this record.', compute='_compute_genealogy_qc', string='FG QC')
    bmr_ids = fields.Many2many('pharma.bmr', compute='_compute_genealogy',
                               string='BMRs', help='Specifies the BMRs for this record.')
    # Deviation / CAPA genealogy relations. This tier depends on
    # pharma_capa_deviation, so these are plain computed relations (no bridge, no
    # runtime guard). They back both the genealogy tags and the smart buttons.
    deviation_ids = fields.Many2many(
        comodel_name='pharma.deviation', help='Specifies the Deviation Ids for this record.',
        compute='_compute_deviation_capa', string='Deviations')
    capa_ids = fields.Many2many(
        comodel_name='pharma.capa', help='Specifies the Capa Ids for this record.',
        compute='_compute_deviation_capa', string='CAPAs')
    deviation_count = fields.Integer(
        string='Deviation Count', help='Specifies the Deviation Count for this record.', compute='_compute_deviation_capa')
    capa_count = fields.Integer(
        string='CAPA Count', help='Specifies the Capa Count for this record.', compute='_compute_deviation_capa')
    oos_investigation_ids = fields.Many2many('pharma.oos.investigation', compute='_compute_genealogy',
                                             string='OOS Investigations',
                                             help='Specifies the OOS Investigations for this record.')
    coa_ids = fields.Many2many('pharma.coa', compute='_compute_genealogy',
                               string='Certificates of Analysis',
                               help='Specifies the Certificates of Analysis for this record.')

    def _compute_genealogy(self):
        """Compile the full backward and forward traceability data for this lot."""
        for lot in self:
            # 1. Productions that produced this lot.
            # The MO link on a finished-goods move line lives on the move
            # (move_id.production_id), not always on the line's own
            # production_id field, so match on both to be reliable.
            produced_sml = self.env['stock.move.line'].search([
                ('lot_id', '=', lot.id),
                '|',
                ('production_id', '!=', False),
                ('move_id.production_id', '!=', False),
            ])
            productions = produced_sml.mapped('production_id') | \
                produced_sml.mapped('move_id.production_id')
            lot.produced_production_ids = productions

            # 2. Raw material lots consumed by these productions. Consumption is
            # not always recorded on the raw moves, so this is resolved through
            # mrp.production._pharma_raw_material_lots() — real consumed lots
            # when present, otherwise the received (incoming-QC) lots of the
            # BOM component products. This powers the Raw Material Traceability
            # tab and every downstream quality relation.
            if productions:
                consumed_lots = self.env['stock.lot']
                for prod in productions:
                    consumed_lots |= prod._pharma_raw_material_lots()
                consumed_lots -= lot
            else:
                consumed_lots = self.env['stock.lot']
            lot.consumed_lot_ids = consumed_lots

            # 3. POs and Vendors for this lot + consumed lots
            all_lots = lot + consumed_lots
            if all_lots:
                incoming_sml = self.env['stock.move.line'].search([
                    ('lot_id', 'in', all_lots.ids),
                    ('picking_id.picking_type_id.code', '=', 'incoming'),
                    ('state', '=', 'done')
                ])
                purchases = incoming_sml.mapped('move_id.purchase_line_id.order_id')
                vendors = purchases.mapped('partner_id')
            else:
                purchases = self.env['purchase.order']
                vendors = self.env['res.partner']
            lot.purchase_order_ids = purchases
            lot.vendor_ids = vendors
            # 1. Delivery Orders
            outgoing_sml = self.env['stock.move.line'].search([
                ('lot_id', '=', lot.id),
                ('picking_id.picking_type_id.code', '=', 'outgoing'),
                ('state', '=', 'done')
            ])
            deliveries = outgoing_sml.mapped('picking_id')
            lot.delivery_order_ids = deliveries

            # 2. Customers
            lot.customer_ids = deliveries.mapped('partner_id')

            # 3. Invoices
            if hasattr(deliveries, 'sale_id'):
                sales = deliveries.mapped('sale_id')
                invoices = sales.mapped('invoice_ids')
            else:
                invoices = self.env['account.move']
            lot.invoice_ids = invoices
            # QC test orders and OOS investigations span the finished lot AND
            # its consumed raw-material lots, so incoming (raw material) QC and
            # its OOS investigations appear in the genealogy Quality tab — not
            # only the finished lot's in-process/FG tests.
            quality_lots = lot + consumed_lots
            lot.qc_test_ids = self.env['pharma.qc.test.order'].search([('lot_id', 'in', quality_lots.ids)])
            lot.oos_investigation_ids = self.env['pharma.oos.investigation'].search([('result_line_id.test_order_id.lot_id', 'in', quality_lots.ids)])
            # CoAs are issued per finished lot only (raw materials have no CoA).
            lot.coa_ids = self.env['pharma.coa'].search([('lot_id', '=', lot.id)])
            lot.bmr_ids = self.env['pharma.bmr'].search([('production_id', 'in', productions.ids)])

    @api.depends('bmr_ids', 'consumed_lot_ids')
    def _compute_deviation_capa(self):
        """Deviations and CAPAs for this lot and its consumed raw-material lots."""
        for lot in self:
            productions = lot.bmr_ids.mapped('production_id')
            quality_lots = lot | lot.consumed_lot_ids
            devs = self.env['pharma.deviation'].search([
                '|', ('batch_id', 'in', productions.ids), ('lot_id', 'in', quality_lots.ids)
            ])
            capas = self.env['pharma.capa'].search(
                [('deviation_id', 'in', devs.ids)]) if devs else self.env['pharma.capa']
            lot.deviation_ids = devs.ids
            lot.capa_ids = capas.ids
            lot.deviation_count = len(devs)
            lot.capa_count = len(capas)

    def action_view_lot_deviations(self):
        """Executes the action_view_lot_deviations operation."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Deviations',
            'res_model': 'pharma.deviation',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.deviation_ids.ids)],
        }

    def action_view_lot_capas(self):
        """Executes the action_view_lot_capas operation."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'CAPAs',
            'res_model': 'pharma.capa',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.capa_ids.ids)],
        }

    def _compute_genealogy_qc(self):
        """Splits QC tests into categories based on stage for genealogy view."""
        for lot in self:
            # Stage values come from pharma.qc.test.order: 'incoming' (raw
            # material), 'inprocess' (IPQC) and 'finished' (FG).
            lot.incoming_qc_ids = lot.qc_test_ids.filtered(lambda q: q.stage == 'incoming')
            lot.ipqc_ids = lot.qc_test_ids.filtered(lambda q: q.stage == 'inprocess')
            lot.fg_qc_ids = lot.qc_test_ids.filtered(lambda q: q.stage == 'finished')
