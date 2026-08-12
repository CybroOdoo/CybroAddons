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
from odoo.tools.translate import _

class StockLot(models.Model):
    """Extends stock.lot with pharma lot status, expiry, and QA traceability."""
    _inherit = 'stock.lot'
    lot_status = fields.Selection(
        selection=[
            ('quarantine', 'Quarantine'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('on_hold', 'On Hold'),
            ('released', 'Released (FG)'),
            ('recalled', 'Recalled'),
        ],
        string='Lot Status',
        default='quarantine',
        required=True,
        tracking=True,
        index=True,
        help='Controls which operations are permitted for this lot. '
             'Quarantine/Rejected/On Hold/Recalled lots are blocked from '
             'production and dispatch.',
    )
    status_changed_by = fields.Many2one(
        comodel_name='res.users',
        string='Status Changed By',
        copy=False,
        tracking=True,
            help='Specifies the Status Changed By for this record.',
    )

    status_changed_on = fields.Datetime(
        string='Status Changed On',
        copy=False,
        tracking=True,
            help='Specifies the Status Changed On for this record.',
    )
    expiry_date = fields.Date(
        string='Expiry Date',
        tracking=True,
        help='Expiry date of this lot, calculated from manufacture date and shelf life.',
    )

    manufacture_date = fields.Date(
        string='Manufacture Date',
        tracking=True,
            help='Specifies the Manufacture Date for this record.',
    )

    retest_date = fields.Date(
        string='Re-test Date',
        tracking=True,
        help='Date by which this lot must be re-tested for continued use.',
    )
    qc_test_count = fields.Integer(
        string='QC Tests',
        compute='_compute_qc_test_count',
        help='Specifies the QC Tests for this record.',
    )

    def _compute_qc_test_count(self):
        """Calculates the number of Quality Control Test Orders associated with this lot."""
        for lot in self:
            lot.qc_test_count = self.env['pharma.qc.test.order'].search_count([('lot_id', '=', lot.id)])

    def action_view_qc_tests(self):
        """Open all QC Test Orders linked to this lot."""
        self.ensure_one()
        return {
            'name': 'QC Test Orders',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'pharma.qc.test.order',
            'domain': [('lot_id', '=', self.id)],
            'context': {'default_lot_id': self.id},
        }
    vendor_coa = fields.Binary(
        string="Vendor CoA",
        attachment=True,
        help="Vendor's Certificate of Analysis attached at goods receipt.",
    )

    vendor_coa_filename = fields.Char(
        string='CoA Filename',

            help='Specifies the CoA Filename for this record.',
    )

    vendor_lot_number = fields.Char(
        string="Vendor's Lot Number",
        help="The lot/batch number as printed on the vendor's label or CoA.",
        tracking=True,
    )
    disposition_remarks = fields.Text(
        string='Disposition Remarks',
        tracking=True,
        help='QA justification for releasing, rejecting, or holding this lot.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Log the user and timestamp when a lot status is set."""
        for vals in vals_list:
            if vals.get('lot_status'):
                vals['status_changed_by'] = self.env.user.id
                vals['status_changed_on'] = fields.Datetime.now()
        return super().create(vals_list)

    def write(self, vals):
        """Log the user and timestamp whenever the lot status changes."""
        if 'lot_status' in vals:
            vals['status_changed_by'] = self.env.user.id
            vals['status_changed_on'] = fields.Datetime.now()
        return super().write(vals)
    def action_approve_lot(self):
        """Set the lot status to Approved for use or dispatch."""
        self.write({'lot_status': 'approved'})

    def action_reject_lot(self):
        """Changes the lot status to 'Rejected', blocking it from production and dispatch."""
        self.write({'lot_status': 'rejected'})

    def _pharma_create_disposition_transfer(self, dest_location):
        """Move the lot's on-hand stock to the QC-disposition destination location."""
        self.ensure_one()
        company = self.company_id or self.env.company
        if not dest_location:
            return False

        # On-hand quants of this lot, excluding only the EXACT destination so
        # stock already there is not moved again. Matched exactly, not with
        # `child_of`: putaway drops lines into a sub-area below the destination,
        # and a `child_of` exclusion would read those as "already at
        # destination" and skip the move, leaving rejected material mixed in.
        quants = self.env['stock.quant'].search([
            ('lot_id', '=', self.id),
            ('location_id.usage', '=', 'internal'),
            ('location_id', '=', dest_location.id),
        ])
        already_at_dest = quants
        quants = self.env['stock.quant'].search([
            ('lot_id', '=', self.id),
            ('location_id.usage', '=', 'internal'),
            ('quantity', '>', 0),
        ]) - already_at_dest
        if not quants:
            return False

        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('company_id', '=', company.id),
        ], limit=1) or self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
        ], limit=1)
        if not picking_type:
            picking_type = self.env['stock.picking.type'].with_context(
                active_test=False).search([
                    ('code', '=', 'internal'),
                    ('company_id', '=', company.id),
                ], limit=1) or self.env['stock.picking.type'].with_context(
                active_test=False).search([
                    ('code', '=', 'internal'),
                ], limit=1)
        if not picking_type:
            return False

        # Group the quantity to move by its current source location, so a lot
        # spread across several locations is fully relocated.
        qty_by_source = {}
        for quant in quants:
            qty_by_source[quant.location_id] = \
                qty_by_source.get(quant.location_id, 0.0) + quant.quantity
        qty_by_source = {loc: qty for loc, qty in qty_by_source.items() if qty > 0}
        if not qty_by_source:
            return False

        source_locations = list(qty_by_source)
        # NB: stock.move has no ``name`` field in Odoo 19 (its rec_name is the
        # computed ``reference``); passing it raises ValueError on create.
        move_vals = [(0, 0, {
            'product_id': self.product_id.id,
            'product_uom_qty': qty,
            'product_uom': self.product_id.uom_id.id,
            'location_id': source_location.id,
            'location_dest_id': dest_location.id,
            'company_id': company.id,
        }) for source_location, qty in qty_by_source.items()]
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': source_locations[0].id,
            'location_dest_id': dest_location.id,
            'company_id': company.id,
            'origin': _('QC Disposition: %s', self.name),
            'move_ids': move_vals,
        })
        # Skip the GMP consume-block check: this move IS the QA disposition.
        picking = picking.with_context(pharma_qa_disposition=True)
        picking.action_confirm()
        for move in picking.move_ids:
            qty = qty_by_source.get(move.location_id, 0.0)
            move.move_line_ids.unlink()
            put_location = dest_location._get_putaway_strategy(
                self.product_id, quantity=qty) or dest_location
            self.env['stock.move.line'].create({
                'move_id': move.id,
                'picking_id': picking.id,
                'product_id': self.product_id.id,
                'product_uom_id': self.product_id.uom_id.id,
                'lot_id': self.id,
                'quantity': qty,
                'picked': True,
                'location_id': move.location_id.id,
                # Only the line drops to the sub-area; the picking and the move
                # header stay on the configured disposition area.
                'location_dest_id': put_location.id,
                'company_id': company.id,
            })
            move.picked = True
        picking._action_done()
        return picking
