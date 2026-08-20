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


class PharmaCoA(models.Model):
    """Certificate of Analysis for a released batch."""
    _name = 'pharma.coa'
    _description = 'Certificate of Analysis'
    _inherit = ['mail.thread']

    name = fields.Char(string='Reference', required=True, tracking=True, default='New', copy=False,
        help='Specifies the Reference for this record.')
    batch_id = fields.Many2one('mrp.production', string='Production Batch', tracking=True,
        help='Specifies the Production Batch for this record.')
    product_id = fields.Many2one('product.template', string='Product', tracking=True,
        help='Specifies the Product for this record.')
    lot_id = fields.Many2one('stock.lot', string='Lot/Batch', tracking=True,
        help='Specifies the Lot/Batch for this record.')
    released_by = fields.Many2one('res.users', string='Released By', tracking=True,
        help='Specifies the Released By for this record.')
    release_date = fields.Datetime(string='Release Date', tracking=True,
        help='Specifies the Release Date for this record.')
    qc_test_order_id = fields.Many2one('pharma.qc.test.order', string='QC Test Order', tracking=True,
        help='Specifies the QC Test Order for this record.')
    is_locked = fields.Boolean(string='Locked', default=False, tracking=True,
        help='Specifies the Locked for this record.')
    coa_line_ids = fields.One2many('pharma.coa.line', 'coa_id', string='Test Results',
        help='Specifies the Test Results for this record.')
    qc_result_ids = fields.Many2many(help='Specifies the Qc Result Ids for this record.',
        comodel_name='pharma.qc.result.line',
        compute='_compute_related_quality_records',
        string='All QC Results'
    )
    qc_test_ids = fields.Many2many(help='Specifies the Qc Test Ids for this record.',
        comodel_name='pharma.qc.test.order',
        compute='_compute_related_quality_records',
        string='All QC Tests'
    )
    oos_ids = fields.Many2many(help='Specifies the Oos Ids for this record.',
        comodel_name='pharma.oos.investigation',
        compute='_compute_related_quality_records',
        string='OOS Investigations'
    )
    ipqc_ids = fields.Many2many(
        comodel_name='pharma.ipqc.result',
        compute='_compute_related_quality_records',
        string='IPQC Results',
        help='In-Process Quality Control check results for this batch.',
    )
    # Deviation / CAPA relations for the batch. This tier depends on
    # pharma_capa_deviation, so pharma.deviation / pharma.capa are always present
    # and these are plain computed relations (no bridge, no runtime guard). They
    # back both the inline-list tabs and the smart buttons on the CoA form.
    deviation_ids = fields.Many2many(help='Specifies the Deviation Ids for this record.',
        comodel_name='pharma.deviation',
        compute='_compute_deviation_capa', string='Deviations')
    capa_ids = fields.Many2many(help='Specifies the Capa Ids for this record.',
        comodel_name='pharma.capa',
        compute='_compute_deviation_capa', string='CAPAs')
    deviation_count = fields.Integer(help='Specifies the Deviation Count for this record.',
        string='Deviation Count', compute='_compute_deviation_capa')
    capa_count = fields.Integer(help='Specifies the Capa Count for this record.',
        string='CAPA Count', compute='_compute_deviation_capa')

    @api.depends('batch_id', 'lot_id')
    def _compute_deviation_capa(self):
        """Deviations and CAPAs for the batch and its consumed raw-material lots."""
        for rec in self:
            devs = self.env['pharma.deviation']
            capas = self.env['pharma.capa']
            lot_ids = self.env['stock.lot']
            if rec.lot_id:
                lot_ids |= rec.lot_id
            if rec.batch_id:
                # Inferred raw-material lots of the batch (BOM components) so
                # raw-material deviations/CAPAs surface alongside finished ones.
                lot_ids |= rec.batch_id._pharma_raw_material_lots()
            # Build the domain so an unset batch_id never degrades to
            # ('batch_id', '=', False), which would match unrelated deviations.
            domain = []
            if rec.batch_id and lot_ids:
                domain = ['|', ('batch_id', '=', rec.batch_id.id), ('lot_id', 'in', lot_ids.ids)]
            elif rec.batch_id:
                domain = [('batch_id', '=', rec.batch_id.id)]
            elif lot_ids:
                domain = [('lot_id', 'in', lot_ids.ids)]
            if domain:
                devs = self.env['pharma.deviation'].search(domain)
                capas = self.env['pharma.capa'].search(
                    [('deviation_id', 'in', devs.ids)])
            rec.deviation_ids = devs.ids
            rec.capa_ids = capas.ids
            rec.deviation_count = len(devs)
            rec.capa_count = len(capas)

    def action_view_coa_deviations(self):
        """Open the batch deviations from the CoA smart button."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Deviations',
            'res_model': 'pharma.deviation',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.deviation_ids.ids)],
        }

    def action_view_coa_capas(self):
        """Open the batch CAPAs from the CoA smart button."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'CAPAs',
            'res_model': 'pharma.capa',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.capa_ids.ids)],
        }

    @api.depends('batch_id', 'lot_id')
    def _compute_related_quality_records(self):
        """Executes the _compute_related_quality_records operation."""
        for rec in self:
            lot_ids = self.env['stock.lot']
            if rec.lot_id:
                lot_ids |= rec.lot_id
            if rec.batch_id:
                # Raw-material lots (inferred from the batch's BOM components —
                # see mrp.production._pharma_raw_material_lots) so raw QC/OOS
                # appear alongside the finished-goods results.
                lot_ids |= rec.batch_id._pharma_raw_material_lots()

            if rec.batch_id:
                bmr = self.env['pharma.bmr'].search([('production_id', '=', rec.batch_id.id)], limit=1)
                rec.ipqc_ids = bmr.ipqc_ids.ids if bmr else False
            else:
                rec.ipqc_ids = False

            if lot_ids:
                qc_tests = self.env['pharma.qc.test.order'].search([('lot_id', 'in', lot_ids.ids)])
                rec.qc_test_ids = qc_tests.ids
                rec.qc_result_ids = qc_tests.mapped('result_line_ids').ids

                oos = self.env['pharma.oos.investigation'].search([('result_line_id.test_order_id', 'in', qc_tests.ids)])
                rec.oos_ids = oos.ids
            else:
                rec.qc_test_ids = False
                rec.qc_result_ids = False
                rec.oos_ids = False

    def _get_report_deviations(self):
        """Return the batch deviations for the CoA report."""
        self.ensure_one()
        return self.deviation_ids

    def _get_report_capas(self):
        """Return the batch CAPAs for the CoA report."""
        self.ensure_one()
        return self.capa_ids

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate the sequence and set initial tracking fields."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('pharma.coa') or 'New'
        return super().create(vals_list)

    def write(self, vals):
        """Override write to enforce business rules and protect locked CoA records."""
        from odoo.exceptions import ValidationError
        allowed_fields = {'message_follower_ids', 'message_ids', 'access_token', 'message_attachment_count'}
        if any(f not in allowed_fields for f in vals):
            for rec in self:
                if rec.is_locked:
                    raise ValidationError("Certificates of Analysis are permanently locked and cannot be modified.")
        return super().write(vals)

    def unlink(self):
        """Prevent deletion of CoA records to preserve the audit trail."""
        from odoo.exceptions import ValidationError
        for rec in self:
            if rec.is_locked:
                raise ValidationError("Certificates of Analysis are permanent records and cannot be deleted.")
        return super().unlink()
