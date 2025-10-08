# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhin K(odoo@cybrosys.com)
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
from odoo import api, fields, models


class BaseDocumentLayout(models.TransientModel):
    """Model is inherited to add required field
    and to add function to display the preview"""
    _inherit = 'base.document.layout'

    base_layout_purchase = fields.Selection(
        related='company_id.base_layout_purchase',
        readonly=False, string='Base Layout Purchase',
        required=True,
        help='Select the base layout for the Purchase module.')
    document_layout_purchase_id = fields.Many2one(
        related='company_id.document_layout_purchase_id', readonly=False,
        string='Document Layout Purchase ID',
        help='Choose the document layout for the Purchase module.')

    @api.depends('report_layout_id', 'logo', 'font', 'primary_color',
                 'secondary_color', 'report_header', 'report_footer',
                 'base_layout_purchase', 'document_layout_purchase_id')
    def _compute_preview(self):
        """Compute a qweb based preview to display on the wizard """
        styles = self._get_asset_style()
        for wizard in self:
            ir_ui_view = wizard.env['ir.ui.view']
            preview_css = self._get_css_for_preview(styles, wizard.id)
            if wizard.report_layout_id:
                style = wizard.document_layout_purchase_id
                if wizard.base_layout_purchase == 'default':
                    wizard.preview = ir_ui_view._render_template(
                        'purchase_format_editor.'
                        'report_preview_default_purchase',
                        {'company': wizard, 'preview_css': preview_css,"style": style})
                elif wizard.base_layout_purchase == 'normal':
                    wizard.preview = ir_ui_view._render_template(
                        'purchase_format_editor.'
                        'report_preview_normal_purchase',
                        {'company': wizard, 'preview_css': preview_css, }
                    )
                elif wizard.base_layout_purchase == 'modern':
                    wizard.preview = ir_ui_view._render_template(
                        'purchase_format_editor.'
                        'report_preview_modern_purchase',
                        {'company': wizard, 'preview_css': preview_css, }
                    )
                elif wizard.base_layout_purchase == 'old':
                    wizard.preview = ir_ui_view._render_template(
                        'purchase_format_editor.'
                        'report_preview_old_purchase',
                        {'company': wizard, 'preview_css': preview_css, })

    def print_pdf(self):
        """This function replaces the existing function to print
        the preview of pdf.Returns: self.id to the controller and
        the controller makes the response to download the pdf"""
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': f'/purchase/pdf/preview?params={self.id}',
        }
