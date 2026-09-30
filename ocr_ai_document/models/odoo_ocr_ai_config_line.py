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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, models, fields,_
from odoo.exceptions import ValidationError


class OdooOcrAiConfigLine(models.Model):
    """One row in the field-mapping table: AI field title → Odoo field."""
    _name = 'odoo.ocr.ai.config.line'
    _description = 'OCR AI Config Line'

    model_id = fields.Many2one(
        comodel_name='odoo.ocr.ai.config',
        ondelete='cascade',
        help='The OCR AI Configuration this mapping line belongs to.',
    )
    title = fields.Char(
        string='AI Field Title',
        help='The exact label the OCR AI service will use to identify this '
             'entity when reading the document, e.g. "Invoice Number".',
    )
    ocr_field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        string='Odoo Field',
        help='The Odoo field that the extracted value will be written to.',
    )
    ttype = fields.Selection(
        related='ocr_field_id.ttype',
        readonly=True,
        help='Field type of the selected Odoo Field, used to determine '
             'whether Related Child Fields are required.',
    )
    ocr_ir_field_ids = fields.Many2many(
        comodel_name='ir.model.fields',
        string='Related Child Fields',
        help='For One2many fields (e.g. invoice/order lines), the set of '
             'sub-fields the OCR service should extract for each line. '
             'Not needed for simple many2one fields.',
    )
    ocr_ir_field_ids_domain = fields.Char(
        compute='_compute_ocr_ir_field_ids_domain',
        help='Technical field used to restrict the Related Child Fields '
             'selection to fields of the related model.',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Determines the order in which fields are sent to and '
             'processed from the OCR AI service.',
    )
    create_if_not_found = fields.Boolean(
        string='Create Record if Not Found?',
        help='If checked, a new record (e.g. Partner, Product) will be '
             'created automatically when no matching record is found for '
             'the extracted value.',
    )

    @api.depends('ocr_field_id')
    def _compute_ocr_ir_field_ids_domain(self):
        """Compute the domain for related child fields."""
        for rec in self:
            if rec.ocr_field_id and rec.ocr_field_id.relation:
                related_model = self.env['ir.model'].search(
                    [('model', '=', rec.ocr_field_id.relation)], limit=1)
                rec.ocr_ir_field_ids_domain = str([
                    ('model_id', '=', related_model.id),
                    ('ttype', 'in', [
                        'char', 'date', 'integer', 'selection', 'monetary',
                        'float', 'one2many', 'text', 'many2many', 'many2one',
                    ]),
                ])
            else:
                rec.ocr_ir_field_ids_domain = str([('model_id', '=', False)])

    @api.constrains('ocr_field_id', 'ocr_ir_field_ids')
    def _check_relational_child_fields(self):
        """
        Child fields are required only for one2many (line items).
        many2one fields like currency_id or partner_id are matched by a simple
        string value and do NOT require child fields.
        """
        for rec in self:
            if rec.ocr_field_id.ttype == 'one2many' and not rec.ocr_ir_field_ids:
                raise ValidationError(_(
                    'For One2many fields, "Related Child Fields" is mandatory. '
                    'Please update the field mapping for "%s".'
                ) % rec.title)

    @api.constrains('ocr_field_id', 'model_id')
    def _check_field_uniqueness_within_config(self):
        """Ensure each field is mapped only once per configuration."""
        for rec in self:
            if rec.ocr_field_id and rec.model_id:
                duplicate = self.search_count([
                    ('ocr_field_id', '=', rec.ocr_field_id.id),
                    ('model_id', '=', rec.model_id.id),
                    ('id', '!=', rec.id),
                ])
                if duplicate:
                    raise ValidationError(_(
                        'The field "%s" is already mapped in another line of this configuration.'
                    ) % rec.ocr_field_id.field_description)