# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class BaseDocumentLayout(models.TransientModel):  # pylint: disable=no-wizard-in-models
    """Inheriting the base document layout model"""
    _inherit = 'base.document.layout'

    base_layout = fields.Selection(
        related='company_id.base_layout',
        string='Invoice Document Layout',
        readonly=False,
        help="Base layout selection field inside "
             "document layout model")
    document_layout_id = fields.Many2one(
        related='company_id.document_layout_id',
        string='Invoice Layout Configuration',
        readonly=False,
        help="custom document layouts")
    is_euro_paperformat = fields.Boolean(
        compute='_compute_is_euro_paperformat',
        help="Technical field to identify the standard euro paper format.")

    @api.depends('paperformat_id')
    def _compute_is_euro_paperformat(self):
        """Avoid relying on database-specific ids for standard
        paper formats.
        """
        euro_paperformat = self.env.ref(
            'base.paperformat_euro', raise_if_not_found=False
        )
        for wizard in self:
            wizard.is_euro_paperformat = bool(
                euro_paperformat and wizard.paperformat_id == euro_paperformat
            )

    @api.depends('base_layout', 'document_layout_id')
    def _compute_preview(self):
        """Compute preview using base and custom layout templates."""
        res = super()._compute_preview()
        styles = self._get_asset_style()
        for wizard in self:
            if not wizard.base_layout:
                wizard.preview = False
            elif (
                wizard.report_layout_id
                and wizard.base_layout in ('normal', 'modern', 'old')
            ):
                template = wizard._get_preview_template()
                render_info = wizard._get_render_information(styles)
                wizard.preview = wizard.env['ir.ui.view']._render_template(
                    template, render_info
                )
        return res

    def _get_preview_template(self):
        """Return the appropriate preview template based on base_layout."""
        self.ensure_one()
        if self.base_layout == 'normal':
            return 'invoice_format_editor.report_preview_normal'
        if self.base_layout == 'modern':
            return 'invoice_format_editor.report_preview_modern'
        if self.base_layout == 'old':
            return 'invoice_format_editor.report_preview_old'
        return super()._get_preview_template()

    @api.onchange('paperformat_id')
    def _onchange_paperformat_id(self):
        """Reset base layout to default when paper format is selected."""
        for wizard in self:
            if wizard.is_euro_paperformat:
                wizard.base_layout = 'default'
