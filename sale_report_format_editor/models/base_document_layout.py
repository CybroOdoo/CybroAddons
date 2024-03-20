# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swathy K S (odoo@cybrosys.com)
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
##############################################################################
from odoo import api, fields, models


class BaseDocumentLayout(models.TransientModel):
    """Inheriting the base document layout model to add some fields"""
    _inherit = 'base.document.layout'

    base_layout = fields.Selection(related='company_id.base_layout',
                                   string="Base Layout", readonly=False,
                                   help="Base layout of current company")
    document_layout_id = fields.Many2one(
        related='company_id.document_layout_id', string="Sale Document Layout",
        readonly=False, help="Sale Document layout of company")
    watermark = fields.Boolean(string='Watermark',
                               help="Enable if you want show "
                                    "watermark on report")
    watermark_show = fields.Selection(
        [('logo', 'Company Logo'), ('name', 'Company Name')],
        default='logo', string="Watermark Show", help="Types of Watermark")

    @api.depends('report_layout_id', 'logo', 'font', 'primary_color',
                 'secondary_color', 'report_header', 'report_footer',
                 'base_layout', 'document_layout_id')
    def _compute_preview(self):
        """ Compute a qweb based preview of selected base layouts to
            display on the wizards """
        styles = self._get_asset_style()
        for wizard in self:
            if wizard.report_layout_id:
                if wizard.base_layout == 'default':
                    preview_css = self._get_css_for_preview(styles, wizard.id)
                    ir_ui_view = wizard.env['ir.ui.view']
                    wizard.preview = ir_ui_view._render_template(
                        'sale_report_format_editor.report_preview_default',
                        {'company': wizard, 'preview_css': preview_css})
                elif wizard.base_layout == 'normal':

                    preview_css = self._get_css_for_preview(styles, wizard.id)
                    ir_ui_view = wizard.env['ir.ui.view']
                    wizard.preview = ir_ui_view._render_template(
                        'sale_report_format_editor.report_preview_normal',
                        {'company': wizard, 'preview_css': preview_css, })
                elif wizard.base_layout == 'modern':
                    preview_css = self._get_css_for_preview(styles, wizard.id)
                    ir_ui_view = wizard.env['ir.ui.view']
                    wizard.preview = ir_ui_view._render_template(
                        'sale_report_format_editor.report_preview_modern',
                        {'company': wizard, 'preview_css': preview_css, })
                elif wizard.base_layout == 'old':
                    preview_css = self._get_css_for_preview(styles, wizard.id)
                    ir_ui_view = wizard.env['ir.ui.view']
                    wizard.preview = ir_ui_view._render_template(
                        'sale_report_format_editor.report_preview_old',
                        {'company': wizard, 'preview_css': preview_css, })
                else:
                    wizard.preview = False
            else:
                wizard.preview = False
