# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_text(self, report_ref, res_ids, data=None):
        """Render the ZPL Label Designer report.
        Resolves the ``zpl.label.template`` and the target records to
        print from ``res_ids``/``data``, then concatenates the generated
        ZPL for each record. Falls back to the template's static sample
        ZPL if no records are resolved, and to the default QWeb-text
        rendering for any other report. """
        data = data or {}
        report = self._get_report_from_name(report_ref)

        if report and report.report_name == 'advanced_zpl_label_designer_print.report_zpl_view':
            res_id_list = res_ids if isinstance(res_ids, list) else [res_ids] if res_ids else []


            template_id = False
            if res_id_list:
                template_id = res_id_list[0]
            elif data:
                template_id = data.get('zpl_template_id') or \
                              data.get('active_ids', [False])[0] or \
                              (data.get('context') and data['context'].get('active_id'))

            template = self.env['zpl.label.template'].browse(template_id)

            if not template.exists():
                return b"^XA^FDTemplate Error^FS^XZ", 'text'

            model_name = template.model_id.model
            record_ids = data.get('product_ids') or data.get('active_ids') or []
            if not record_ids and res_id_list:

                if template_id not in res_id_list:
                    record_ids = res_id_list

            records = self.env[model_name].browse(record_ids)

            # 3. Generate Labels
            if records:
                final_zpl = ""
                for record in records:
                    final_zpl += template.generate_zpl_for_product(record) + "\n"
                return final_zpl.encode('utf-8'), 'text'

            # 4. Fallback for Preview (when clicking 'Preview' on the template itself)
            return template.zpl_content.encode('utf-8'), 'text'

        return super()._render_qweb_text(report_ref, res_ids, data=data)
