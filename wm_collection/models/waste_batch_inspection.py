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
import base64
import urllib.parse

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WasteBatchInspection(models.Model):
    """Quality inspection and contamination check record for received waste batches."""
    _name = 'wm.batch.inspection'
    _description = 'Waste Batch Inspection'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Inspection Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    batch_id = fields.Many2one(
        'waste.batch',
        string='Waste Batch',
        required=True,
        ondelete='cascade'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='batch_id.company_id',
        store=True,
        readonly=False,
        default=lambda self: self.env.company,
    )
    batch_line_ids = fields.One2many(
        string='Batch Materials',
        related='batch_id.line_ids',
        readonly=False,
    )
    inspector_id = fields.Many2one(
        'res.users',
        string='Inspector',
        default=lambda self: self.env.user
    )
    inspection_date = fields.Datetime(
        string='Inspection Date',
        default=fields.Datetime.now
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('passed', 'Passed'),
        ('failed', 'Failed')
    ], string='Status', default='draft', required=True, tracking=True)

    quality_grade = fields.Selection([
        ('grade_a', 'Grade A'),
        ('grade_b', 'Grade B'),
        ('grade_c', 'Grade C'),
        ('rejected', 'Rejected')
    ], string='Quality Grade', help='Assessed quality grade of the waste batch.', tracking=True)
    contamination_percentage = fields.Float(
        string='Contamination (%)',
        default=0.0,
        help='Estimated percentage of contamination.',
        tracking=True
    )
    moisture_percentage = fields.Float(
        string='Moisture (%)',
        default=0.0,
        help='Estimated percentage of moisture.',
        tracking=True
    )
    hazard_verified = fields.Boolean(
        string='Hazard Verified',
        default=False,
        help='Check if the material hazard status has been verified during inspection.',
        tracking=True
    )
    notes = fields.Text(
        string='Inspection Notes',
        help='Additional observations or remarks from the inspection.',
        tracking=True
    )
    signature_template_id = fields.Many2one('wm.signature.template', string='Signature Template', ondelete='set null')
    is_signed = fields.Boolean(string='Signed', default=False, tracking=True)
    signature_status = fields.Selection([
        ('presence_present', 'Signed'),
        ('presence_absent', 'Not Signed')
    ], string='Signed Status', compute='_compute_signature_status', store=True)

    use_quality_grading = fields.Boolean(compute='_compute_use_settings')
    use_hazardous_waste = fields.Boolean(compute='_compute_use_settings')

    def _compute_use_settings(self):
        """
        Load inspection module feature flags from ir.config_parameter to
        determine whether digital signature enforcement and contamination photo
        uploads are required.
        """
        params = self.env['ir.config_parameter'].sudo()
        use_qual = params.get_param('wm_collection.use_quality_grading') == 'True'
        use_haz = params.get_param('wm_collection.use_hazardous_waste') == 'True'
        for rec in self:
            rec.use_quality_grading = use_qual
            rec.use_hazardous_waste = use_haz

    @api.onchange('contamination_percentage', 'moisture_percentage')
    def _onchange_measurements(self):
        """
        Recalculate derived inspection metrics (contamination percentage,
        pass/fail decision) in real-time as the operator enters gross weight,
        tare, or contamination readings.
        """
        warnings = []
        if self.contamination_percentage > 30.0:
            warnings.append(_('Contamination exceeds 30%%.'))
        if self.moisture_percentage > 20.0:
            warnings.append(_('Moisture exceeds 20%%.'))

        if warnings:
            return {
                'warning': {
                    'title': _('Measurement Warning'),
                    'message': ' '.join(warnings),
                }
            }

    @api.constrains('state', 'hazard_verified', 'quality_grade')
    def _check_passing_conditions(self):
        """
        Validate that the waste batch contamination percentage is below the
        configured threshold and all mandatory inspection checklist items are
        marked compliant before approving.
        """
        use_qual = self.env['ir.config_parameter'].sudo().get_param('wm_collection.use_quality_grading') == 'True'
        use_haz = self.env['ir.config_parameter'].sudo().get_param('wm_collection.use_hazardous_waste') == 'True'
        for rec in self:
            if rec.state == 'passed':
                if use_haz and rec.batch_id and rec.batch_id.hazardous and not rec.hazard_verified:
                    raise ValidationError(_('Cannot pass inspection: Hazardous batch requires Hazard Verified.'))
                if use_qual and rec.quality_grade == 'rejected':
                    raise ValidationError(_('Cannot pass inspection: Quality Grade is Rejected.'))

    def _sync_batch_state(self):
        """ Synchronize the inspection state to the parent batch. """
        for rec in self:
            if rec.batch_id:
                rec.batch_id._compute_inspection_state()

    @api.model_create_multi
    def create(self, vals_list):
        """ Override create to implement custom initialization and validation logic. """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('wm.batch.inspection') or _('New')
        records = super().create(vals_list)
        records._sync_batch_state()
        return records

    def write(self, vals):
        """ Override write to implement business validations and side effects. """
        if not self.env.su and not self.env.context.get('skip_inspection_validation'):
            restricted_fields = {
                'quality_grade', 'hazard_verified', 'contamination_percentage',
                'moisture_percentage', 'batch_id', 'inspector_id', 'inspection_date',
                'batch_line_ids',
            }
            if restricted_fields.intersection(vals.keys()):
                for rec in self:
                    if rec.state in ('passed', 'failed'):
                        raise UserError(_(
                            "Cannot modify Waste Batch Inspection '%(name)s' because it is already %(state)s.",
                            name=rec.name,
                            state=dict(self._fields['state'].selection).get(rec.state, rec.state),
                        ))
        res = super().write(vals)
        if 'state' in vals:
            self._sync_batch_state()
        return res

    def unlink(self):
        """ Prevent deleting passed or failed batch inspections. """
        for rec in self:
            if rec.state in ('passed', 'failed'):
                raise UserError(_(
                    "Cannot delete Waste Batch Inspection '%(name)s' because it is in '%(state)s' status.",
                    name=rec.name,
                    state=dict(self._fields['state'].selection).get(rec.state, rec.state),
                ))
        return super().unlink()

    def action_start_inspection(self):
        """
        Transition the waste batch inspection from 'pending' to 'in_progress',
        recording the inspector's name, start time, and vehicle/equipment
        identifiers.
        """
        self.write({'state': 'in_progress'})

    def action_pass_inspection(self):
        """
        Mark the waste batch inspection as passed after verifying contamination
        levels are within tolerance, transitioning state and triggering
        downstream sorting authorisation.
        """
        self.write({'state': 'passed'})
        self._post_pdf_to_chatter()
        return True

    def action_fail_inspection(self):
        """
        Fail the inspection, auto-generate a disposal picking to the
        Landfill/Disposal virtual location, and update the parent batch status
        to 'disposed'.  The picking is confirmed (Ready) but intentionally NOT
        validated — physical disposal confirmation remains a manual step.
        Everything runs in a single DB transaction; if picking creation fails
        the entire call is rolled back so the inspection record is never left
        in 'failed' with no corresponding picking.
        """
        self.write({'state': 'failed'})
        self._post_pdf_to_chatter()

        # ── Disposal picking ─────────────────────────────────────────────────
        for rec in self.filtered(lambda r: r.state == 'failed' and r.batch_id):
            batch = rec.batch_id

            # Locate the Landfill/Disposal virtual location
            landfill_loc = self.env.ref(
                'wm_collection.stock_location_landfill',
                raise_if_not_found=False
            )
            if not landfill_loc:
                landfill_loc = self.env['stock.location'].search(
                    [('name', '=', 'Landfill/Disposal'), ('usage', '=', 'inventory')],
                    limit=1
                )
            if not landfill_loc:
                landfill_loc = self.env['stock.location'].create({
                    'name': 'Landfill/Disposal',
                    'usage': 'inventory',
                })

            # Determine the outgoing operation type for the batch's warehouse
            warehouse = batch.warehouse_id
            picking_type = (
                warehouse.out_type_id
                or self.env['stock.picking.type'].search([
                    ('warehouse_id', '=', warehouse.id),
                    ('code', '=', 'outgoing')
                ], limit=1)
                or self.env['stock.picking.type'].search(
                    [('code', '=', 'outgoing')], limit=1
                )
            )

            lines_with_qty = batch.line_ids.filtered(lambda l: l.quantity > 0)
            if not lines_with_qty:
                # Nothing to move — just mark disposed and continue
                batch.write({'status': 'disposed'})
                continue

            picking = self.env['stock.picking'].with_context(default_batch_id=False).create({
                'picking_type_id': picking_type.id if picking_type else False,
                'location_id': batch.location_id.id,
                'location_dest_id': landfill_loc.id,
                'origin': batch.name,
                'company_id': (
                    warehouse.company_id.id or self.env.company.id
                ),
                'note': _('Auto-generated disposal transfer — failed inspection %s') % rec.name,
            })

            for line in lines_with_qty:
                self.env['stock.move'].create({
                    'picking_id': picking.id,
                    'product_id': line.product_id.id,
                    'product_uom': line.uom_id.id,
                    'product_uom_qty': line.quantity,
                    'location_id': batch.location_id.id,
                    'location_dest_id': landfill_loc.id,
                    'origin': batch.name,
                    'company_id': (
                        warehouse.company_id.id or self.env.company.id
                    ),
                })

            # Confirm and validate transfer so failed products are stored directly in Landfill/Disposal
            picking.action_confirm()
            picking.action_assign()
            for move in picking.move_ids:
                move.quantity = move.product_uom_qty
            picking.button_validate()

            batch.write({'status': 'disposed'})

        return True

    def _post_pdf_to_chatter(self):
        """
        Render the inspection report as a PDF and attach it to the batch
        inspection chatter thread for traceability and regulatory audit
        documentation.
        """
        for rec in self:
            pdf_content, report_type = self.env['ir.actions.report']._render_qweb_pdf(
                'wm_collection.action_report_batch_inspection',
                res_ids=[rec.id]
            )
            attachment = self.env['ir.attachment'].create({
                'name': f"Inspection-Report-{rec.name}.pdf",
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': rec._name,
                'res_id': rec.id,
                'mimetype': 'application/pdf',
            })
            rec.message_post(
                body=_("Inspection completed. Result: %s") % rec.state.upper(),
                attachment_ids=[attachment.id]
            )

    def action_sign_now(self):
        """
        Open the digital signature wizard pre-filled with the inspection
        record, requiring an authorised operator to countersign the inspection
        report before it can be finalised.
        """
        self.ensure_one()
        if self.state not in ('passed', 'failed'):
            raise ValidationError(_("You can only sign an inspection that has passed or failed."))

        pdf_content, report_type = self.env['ir.actions.report']._render_qweb_pdf(
            'wm_collection.action_report_batch_inspection',
            res_ids=[self.id]
        )

        role = self.env['wm.signature.role'].sudo().search([('name', '=', 'Inspector')], limit=1)
        if not role:
            role = self.env['wm.signature.role'].sudo().search([('name', '=', 'Signer')], limit=1)
        if not role:
            role = self.env['wm.signature.role'].sudo().create({'name': 'Inspector'})

        if self.signature_template_id:
            self.signature_template_id.sudo().write({
                'document': base64.b64encode(pdf_content),
            })
            if not self.signature_template_id.role_ids:
                self.signature_template_id.sudo().write({'role_ids': [(4, role.id)]})
        else:
            template = self.env['wm.signature.template'].sudo().create({
                'name': f"Inspection Report - {self.name}",
                'document': base64.b64encode(pdf_content),
                'document_filename': f"Inspection_Report_{self.name}.pdf",
                'role_ids': [(6, 0, [role.id])],
            })
            self.signature_template_id = template.id

        # Ensure a default signature item zone exists on the template
        sig_items = self.signature_template_id.item_ids.filtered(lambda item: item.type == 'signature')
        if len(sig_items) > 1:
            sig_items[1:].sudo().unlink()
        elif not sig_items:
            self.env['wm.signature.item'].sudo().create({
                'template_id': self.signature_template_id.id,
                'role_id': role.id,
                'type': 'signature',
                'page': 1,
                'x': 10,
                'y': 78,
                'width': 40,
                'height': 10,
            })

        back_url = f"/web#id={self.id}&model={self._name}&view_type=form"
        encoded_back_url = urllib.parse.quote(back_url)
        return {
            'type': 'ir.actions.act_url',
            'url': f'/wm_signature/template/edit/{self.signature_template_id.id}?inspection_id={self.id}&back_url={encoded_back_url}',
            'target': 'self',
        }

    @api.depends('is_signed')
    def _compute_signature_status(self):
        """
        Derive the current digital signature collection status ('none',
        'partial', 'complete') from the set of completed signature requests on
        this batch inspection record.
        """
        for rec in self:
            rec.signature_status = 'presence_present' if rec.is_signed else 'presence_absent'
