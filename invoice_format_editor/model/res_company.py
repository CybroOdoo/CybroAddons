# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields, api


class ReportCompanyTemplate(models.Model):
    _inherit = 'res.company'

    base_layout = fields.Selection(
        [('normal', 'Normal'), ('modern', 'Modern'), ('old', 'Old Standard'),
         ('default', 'Default')],
        string="Invoice Document Layout", default="default")
    document_layout_id = fields.Many2one("doc.layout",
                                         string="Invoice Layout Configuration"
                                         )


class TemplateInvoice(models.Model):
    _inherit = 'account.move'

    base_layout = fields.Selection(
        [('normal', 'Normal'), ('modern', 'Modern'), ('old', 'Old Standard'),
         ('default', 'Default')])
    theme_id = fields.Many2one('doc.layout',
                               related='company_id.document_layout_id')


class BaseDocumentLayout(models.TransientModel):
    _inherit = 'base.document.layout'

    base_layout = fields.Selection(related='company_id.base_layout',
                                   readonly=False)
    document_layout_id = fields.Many2one(
        related='company_id.document_layout_id', readonly=False)

    @api.depends('report_layout_id', 'logo', 'font', 'primary_color',
                 'secondary_color', 'report_header', 'report_footer',
                 'base_layout', 'document_layout_id')
    def _compute_preview(self):
        """ compute a qweb based preview to display on the wizard """

        styles = self._get_asset_style()

        for wizard in self:
            if wizard.report_layout_id:
                if wizard.base_layout == 'default':
                    preview_css = self._get_css_for_preview(styles, wizard.id)
                    ir_ui_view = wizard.env['ir.ui.view']
                    wizard.preview = ir_ui_view._render_template(
                        'invoice_format_editor.report_preview_default',
                        {'company': wizard, 'preview_css': preview_css})

                elif wizard.base_layout == 'normal':
                    preview_css = self._get_css_for_preview(styles, wizard.id)
                    ir_ui_view = wizard.env['ir.ui.view']
                    wizard.preview = ir_ui_view._render_template(
                        'invoice_format_editor.report_preview_normal',
                        {'company': wizard, 'preview_css': preview_css, })

                elif wizard.base_layout == 'modern':
                    preview_css = self._get_css_for_preview(styles, wizard.id)
                    ir_ui_view = wizard.env['ir.ui.view']
                    wizard.preview = ir_ui_view._render_template(
                        'invoice_format_editor.report_preview_modern',
                        {'company': wizard, 'preview_css': preview_css, })

                elif wizard.base_layout == 'old':
                    preview_css = self._get_css_for_preview(styles, wizard.id)
                    ir_ui_view = wizard.env['ir.ui.view']
                    wizard.preview = ir_ui_view._render_template(
                        'invoice_format_editor.report_preview_old',
                        {'company': wizard, 'preview_css': preview_css, })

                else:
                    wizard.preview = False
