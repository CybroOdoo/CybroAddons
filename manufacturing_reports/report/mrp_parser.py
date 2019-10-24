# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2014-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Cybrosys Technologies(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import datetime
from openerp.osv import osv
from openerp.report import report_sxw


class MrpReport(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(MrpReport, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_details': self.get_details,
            'get_date': self.get_date,
        })
        self.context = context

    def get_date(self):
        date = datetime.datetime.now()
        return date

    def get_details(self, data):
        lines = []

        if data['filter'] is True:
            if data['filter_user'] is True:

                if len(data['product']) > 0 \
                        and data['stage'] is not False:
                    for k in range(0, len(data['product'])):
                        for l in range(0, len(data['responsible'])):
                            for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                                obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                                if (data['date_from'] <= obj.date_planned) \
                                        and (data['date_to'] >= obj.date_planned) \
                                        and obj.state == data['stage'] \
                                        and obj.product_id.id == data['product'][k] \
                                        and obj.user_id.id == data['responsible'][l]:
                                    lines.append(obj)

                elif len(data['product']) == 0 and data['stage'] is not False:
                    for l in range(0, len(data['responsible'])):
                        for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                            obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                            if (data['date_from'] <= obj.date_planned) \
                                    and (data['date_to'] >= obj.date_planned) \
                                    and obj.state == data['stage'] \
                                    and obj.user_id.id == data['responsible'][l]:
                                lines.append(obj)

                if len(data['product']) > 0 \
                        and data['stage'] is False:
                    for k in range(0, len(data['product'])):
                        for l in range(0, len(data['responsible'])):
                            for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                                obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                                if (data['date_from'] <= obj.date_planned) \
                                        and (data['date_to'] >= obj.date_planned) \
                                        and obj.product_id.id == data['product'][k] \
                                        and obj.user_id.id == data['responsible'][l]:
                                    lines.append(obj)

                if len(data['product']) == 0 \
                        and data['stage'] is False:
                    for l in range(0, len(data['responsible'])):
                        for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                            obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                            if (data['date_from'] <= obj.date_planned) \
                                    and (data['date_to'] >= obj.date_planned) \
                                    and obj.user_id.id == data['responsible'][l]:
                                lines.append(obj)
            if data['filter_user'] is False:
                if len(data['product']) > 0 \
                        and data['stage'] is not False:
                    for k in range(0, len(data['product'])):
                            for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                                obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                                if (data['date_from'] <= obj.date_planned) \
                                        and (data['date_to'] >= obj.date_planned) \
                                        and obj.state == data['stage'] \
                                        and obj.product_id.id == data['product'][k]:
                                    lines.append(obj)

                elif len(data['product']) == 0 and data['stage'] is not False:
                        for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                            obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                            if (data['date_from'] <= obj.date_planned) \
                                    and (data['date_to'] >= obj.date_planned) \
                                    and obj.state == data['stage']:
                                lines.append(obj)

                if len(data['product']) > 0 \
                        and data['stage'] is False:
                    for k in range(0, len(data['product'])):
                            for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                                obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                                if (data['date_from'] <= obj.date_planned) \
                                        and (data['date_to'] >= obj.date_planned) \
                                        and obj.product_id.id == data['product'][k]:
                                    lines.append(obj)

                if len(data['product']) == 0 \
                        and data['stage'] is False:
                        for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                            obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                            if (data['date_from'] <= obj.date_planned) \
                                    and (data['date_to'] >= obj.date_planned):
                                lines.append(obj)

        if data['filter'] is False:
            if data['filter_user'] is True:
                if len(data['product']) > 0 \
                        and data['stage'] is not False:
                    for k in range(0, len(data['product'])):
                        for l in range(0, len(data['responsible'])):
                            for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                                obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                                if obj.state == data['stage'] \
                                        and obj.product_id.id == data['product'][k] \
                                        and obj.user_id.id == data['responsible'][l]:
                                    lines.append(obj)

                elif len(data['product']) == 0 and data['stage'] is not False:
                    for l in range(0, len(data['responsible'])):
                        for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                            obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                            if obj.state == data['stage'] \
                                    and obj.user_id.id == data['responsible'][l]:
                                lines.append(obj)

                if len(data['product']) > 0 \
                        and data['stage'] is False:
                    for k in range(0, len(data['product'])):
                        for l in range(0, len(data['responsible'])):
                            for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                                obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                                if obj.product_id.id == data['product'][k] \
                                        and obj.user_id.id == data['responsible'][l]:
                                    lines.append(obj)

                if len(data['product']) == 0 \
                        and data['stage'] is False:
                    for l in range(0, len(data['responsible'])):
                        for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                            obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                            if obj.user_id.id == data['responsible'][l]:
                                lines.append(obj)
            if data['filter_user'] is False:

                if len(data['product']) > 0 \
                        and data['stage'] is not False:
                    for k in range(0, len(data['product'])):
                        for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                            obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                            if obj.state == data['stage'] \
                                    and obj.product_id.id == data['product'][k]:
                                lines.append(obj)

                elif len(data['product']) == 0 and data['stage'] is not False:
                        for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                            obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                            if obj.state == data['stage']:
                                lines.append(obj)

                if len(data['product']) > 0 \
                        and data['stage'] is False:
                    for k in range(0, len(data['product'])):
                            for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                                obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                                if obj.product_id.id == data['product'][k]:
                                    lines.append(obj)

                if len(data['product']) == 0 \
                        and data['stage'] is False:
                        for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                            obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                            lines.append(obj)

        return lines


class PrintReport(osv.AbstractModel):
    _name = 'report.manufacturing_reports.mrp_pdf'
    _inherit = 'report.abstract_report'
    _template = 'manufacturing_reports.mrp_pdf'
    _wrapped_report_class = MrpReport
