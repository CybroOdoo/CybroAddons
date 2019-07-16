# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import datetime
from openerp.report import report_sxw
from openerp.osv import osv


def get_xls(obj):
    getvals = {
        'name': obj.name,
        'vehicle': obj.vehicle_id.name.name,
        'date_deadline': obj.date_deadline,
        'partner_id': obj.partner_id.name,
        'user_id': obj.user_id.name,
        'amount_total': obj.amount_total,
        'stage_id': obj.stage_id.name,
    }
    return getvals


class CarReport(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(CarReport, self).__init__(cr, uid, name, context=context)
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

        if data['filter_vehicle'] is True:
            if data['filter_user'] is True:

                #  ----------------------- FILTER ON DATE PARTNER STATE SP -------------------------
                if data['filter'] == 'filter_date' and data['filter_partner'] is True \
                        and data['stage_id'] is not False:
                    for k in range(0, len(data['vehicles'])):
                        for j in range(0, len(data['partner_name'])):
                            for l in range(0, len(data['sales_person'])):
                                for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                    obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                    if (data['date_from'] <= obj.date_deadline) \
                                            and (data['date_to'] >= obj.date_deadline) \
                                            and obj.partner_id.id == data['partner_name'][j] \
                                            and obj.stage_id.id == data['stage_id'][0] \
                                            and obj.vehicle_id.name.id == data['vehicles'][k] \
                                            and obj.user_id.id == data['sales_person'][l]:
                                        lines.append(get_xls(obj))

                # ----------------------- FILTER ON DATE AND PARTNER SP -------------------------
                elif data['filter'] == 'filter_date' and data['filter_partner'] is True:
                    for k in range(0, len(data['vehicles'])):
                        for j in range(0, len(data['partner_name'])):
                            for l in range(0, len(data['sales_person'])):
                                for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                    obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                    if (data['date_from'] <= obj.date_deadline) \
                                            and (data['date_to'] >= obj.date_deadline) \
                                            and obj.vehicle_id.name.id == data['vehicles'][k] \
                                            and obj.partner_id.id == data['partner_name'][j] \
                                            and obj.user_id.id == data['sales_person'][l]:
                                        lines.append(get_xls(obj))

                # ----------------------- FILTER ON DATE AND STATE SP-------------------------
                elif data['filter'] == 'filter_date' and data['stage_id'] is not False:
                    for k in range(0, len(data['vehicles'])):
                        for l in range(0, len(data['sales_person'])):
                            for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                if (data['date_from'] <= obj.date_deadline) \
                                        and (data['date_to'] >= obj.date_deadline) \
                                        and obj.stage_id.id == data['stage_id'][0] \
                                        and obj.vehicle_id.name.id == data['vehicles'][k] \
                                        and obj.user_id.id == data['sales_person'][l]:
                                    lines.append(get_xls(obj))

                # ----------------------- FILTER ON PARTNER AND STATE SP-------------------------
                elif data['stage_id'] is not False and data['filter_partner'] is True:
                    for k in range(0, len(data['vehicles'])):
                        for j in range(0, len(data['partner_name'])):
                            for l in range(0, len(data['sales_person'])):
                                for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                    obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                    if obj.stage_id.id == data['stage_id'][0] \
                                            and obj.vehicle_id.name.id == data['vehicles'][k] \
                                            and obj.partner_id.id == data['partner_name'][j] \
                                            and obj.user_id.id == data['sales_person'][l]:
                                        lines.append(get_xls(obj))

                # ----------------------- FILTER ON DATE SP-------------------------
                elif data['filter'] == 'filter_date':
                    for k in range(0, len(data['vehicles'])):
                        for l in range(0, len(data['sales_person'])):
                            for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                if (data['date_from'] <= obj.date_deadline) \
                                        and (data['date_to'] >= obj.date_deadline) \
                                        and obj.vehicle_id.name.id == data['vehicles'][k] \
                                        and obj.user_id.id == data['sales_person'][l]:
                                    lines.append(get_xls(obj))

                # -----------------------  FILTER ON PARTNER SP-------------------------
                elif data['filter_partner'] is True:
                    for k in range(0, len(data['vehicles'])):
                        for j in range(0, len(data['partner_name'])):
                            for l in range(0, len(data['sales_person'])):
                                for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                    obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                    if obj.partner_id.id == data['partner_name'][j] \
                                            and obj.vehicle_id.name.id == data['vehicles'][k] \
                                            and obj.user_id.id == data['sales_person'][l]:
                                        lines.append(get_xls(obj))

                # ----------------------- FILTER ON STATE SP-------------------------
                elif data['stage_id'] is not False:
                    for k in range(0, len(data['vehicles'])):
                        for l in range(0, len(data['sales_person'])):
                            for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                if obj.stage_id.id == data['stage_id'][0] \
                                        and obj.vehicle_id.name.id == data['vehicles'][k] \
                                        and obj.user_id.id == data['sales_person'][l]:
                                    lines.append(get_xls(obj))

                # ------------------------ FILTER ON SP---------------------------------------
                else:
                    for k in range(0, len(data['vehicles'])):
                        for l in range(0, len(data['sales_person'])):
                            for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                if obj.user_id.id == data['sales_person'][l] \
                                        and obj.vehicle_id.name.id == data['vehicles'][k]:
                                    lines.append(get_xls(obj))
            else:
                #  ----------------------- FILTER ON DATE PARTNER STATE -------------------------
                if data['filter'] == 'filter_date' and data['filter_partner'] is True \
                        and data['stage_id'] is not False:
                    for k in range(0, len(data['vehicles'])):
                        for j in range(0, len(data['partner_name'])):
                            for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                if (data['date_from'] <= obj.date_deadline) and (data['date_to'] >= obj.date_deadline) \
                                        and obj.partner_id.id == data['partner_name'][j] \
                                        and obj.vehicle_id.name.id == data['vehicles'][k] \
                                        and obj.stage_id.id == data['stage_id'][0]:
                                    lines.append(get_xls(obj))

                # ----------------------- FILTER ON DATE AND PARTNER -------------------------
                elif data['filter'] == 'filter_date' and data['filter_partner'] is True:
                    for k in range(0, len(data['vehicles'])):
                        for j in range(0, len(data['partner_name'])):
                            for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                if (data['date_from'] <= obj.date_deadline) \
                                        and (data['date_to'] >= obj.date_deadline) \
                                        and obj.vehicle_id.name.id == data['vehicles'][k] \
                                        and obj.partner_id.id == data['partner_name'][j]:
                                    lines.append(get_xls(obj))

                # ----------------------- FILTER ON DATE AND STATE -------------------------
                elif data['filter'] == 'filter_date' and data['stage_id'] is not False:
                    for k in range(0, len(data['vehicles'])):
                        for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                            obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                            if (data['date_from'] <= obj.date_deadline) and (data['date_to'] >= obj.date_deadline) \
                                    and obj.vehicle_id.name.id == data['vehicles'][k] \
                                    and obj.stage_id.id == data['stage_id'][0]:
                                lines.append(get_xls(obj))

                # ----------------------- FILTER ON PARTNER AND STATE -------------------------
                elif data['stage_id'] is not False and data['filter_partner'] is True:
                    for k in range(0, len(data['vehicles'])):
                        for j in range(0, len(data['partner_name'])):
                            for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                if obj.stage_id.id == data['stage_id'][0] \
                                        and obj.vehicle_id.name.id == data['vehicles'][k] \
                                        and obj.partner_id.id == data['partner_name'][j]:
                                    lines.append(get_xls(obj))
                # ----------------------- FILTER ON DATE -------------------------
                elif data['filter'] == 'filter_date':
                    for k in range(0, len(data['vehicles'])):
                        for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                            obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                            if (data['date_from'] <= obj.date_deadline) \
                                    and obj.vehicle_id.name.id == data['vehicles'][k] \
                                    and (data['date_to'] >= obj.date_deadline):
                                lines.append(get_xls(obj))

                # -----------------------  FILTER ON PARTNER -------------------------
                elif data['filter_partner'] is True:
                    for k in range(0, len(data['vehicles'])):
                        for j in range(0, len(data['partner_name'])):
                            for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                if obj.partner_id.id == data['partner_name'][j] \
                                        and obj.vehicle_id.name.id == data['vehicles'][k]:
                                    lines.append(get_xls(obj))

                # ----------------------- FILTER ON STATE -------------------------
                elif data['stage_id'] is not False:

                    for k in range(0, len(data['vehicles'])):
                        for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                            obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                            if obj.stage_id.id == data['stage_id'][0] and obj.vehicle_id.name.id == data['vehicles'][k]:
                                lines.append(get_xls(obj))

                # ----------------------- VEHICLE ONLY -------------------------
                else:
                        for k in range(0, len(data['vehicles'])):
                            for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                if obj.vehicle_id.name.id == data['vehicles'][k]:
                                    lines.append(get_xls(obj))

        else:
            if data['filter_user'] is True:
                #  ----------------------- FILTER ON DATE PARTNER STATE SP -------------------------
                if data['filter'] == 'filter_date' and data['filter_partner'] is True \
                        and data['stage_id'] is not False:
                    for j in range(0, len(data['partner_name'])):
                        for l in range(0, len(data['sales_person'])):
                            for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                if (data['date_from'] <= obj.date_deadline) \
                                        and (data['date_to'] >= obj.date_deadline) \
                                        and obj.partner_id.id == data['partner_name'][j] \
                                        and obj.stage_id.id == data['stage_id'][0] \
                                        and obj.user_id.id == data['sales_person'][l]:
                                    lines.append(get_xls(obj))

                # ----------------------- FILTER ON DATE AND PARTNER SP -------------------------
                elif data['filter'] == 'filter_date' and data['filter_partner'] is True:
                    for j in range(0, len(data['partner_name'])):
                        for l in range(0, len(data['sales_person'])):
                            for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                if (data['date_from'] <= obj.date_deadline) \
                                        and (data['date_to'] >= obj.date_deadline) \
                                        and obj.partner_id.id == data['partner_name'][j] \
                                        and obj.user_id.id == data['sales_person'][l]:
                                    lines.append(get_xls(obj))

                # ----------------------- FILTER ON DATE AND STATE SP-------------------------
                elif data['filter'] == 'filter_date' and data['stage_id'] is not False:
                    for l in range(0, len(data['sales_person'])):
                        for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                            obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                            if (data['date_from'] <= obj.date_deadline) \
                                    and (data['date_to'] >= obj.date_deadline) \
                                    and obj.stage_id.id == data['stage_id'][0] \
                                    and obj.user_id.id == data['sales_person'][l]:
                                lines.append(get_xls(obj))

                # ----------------------- FILTER ON PARTNER AND STATE SP-------------------------
                elif data['stage_id'] is not False and data['filter_partner'] is True:
                    for j in range(0, len(data['partner_name'])):
                        for l in range(0, len(data['sales_person'])):
                            for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                if obj.stage_id.id == data['stage_id'][0] \
                                        and obj.partner_id.id == data['partner_name'][j] \
                                        and obj.user_id.id == data['sales_person'][l]:
                                    lines.append(get_xls(obj))

                # ----------------------- FILTER ON DATE SP-------------------------
                elif data['filter'] == 'filter_date':
                    for l in range(0, len(data['sales_person'])):
                        for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                            obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                            if (data['date_from'] <= obj.date_deadline) \
                                    and (data['date_to'] >= obj.date_deadline) \
                                    and obj.user_id.id == data['sales_person'][l]:
                                lines.append(get_xls(obj))

                # -----------------------  FILTER ON PARTNER SP-------------------------
                elif data['filter_partner'] is True:
                    for j in range(0, len(data['partner_name'])):
                        for l in range(0, len(data['sales_person'])):
                            for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                if obj.partner_id.id == data['partner_name'][j] \
                                        and obj.user_id.id == data['sales_person'][l]:
                                    lines.append(get_xls(obj))

                # ----------------------- FILTER ON STATE SP-------------------------
                elif data['stage_id'] is not False:
                    for l in range(0, len(data['sales_person'])):
                        for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                            obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                            if obj.stage_id.id == data['stage_id'][0] \
                                    and obj.user_id.id == data['sales_person'][l]:
                                lines.append(get_xls(obj))

                # ------------------------ FILTER ON SP---------------------------------------
                else:
                    for l in range(0, len(data['sales_person'])):
                        for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                            obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                            if obj.user_id.id == data['sales_person'][l]:
                                lines.append(get_xls(obj))
            else:
                #  ----------------------- FILTER ON DATE PARTNER STATE -------------------------
                if data['filter'] == 'filter_date' and data['filter_partner'] is True \
                        and data['stage_id'] is not False:
                    for j in range(0, len(data['partner_name'])):
                        for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                            obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                            if (data['date_from'] <= obj.date_deadline) and (data['date_to'] >= obj.date_deadline) \
                                    and obj.partner_id.id == data['partner_name'][j] \
                                    and obj.stage_id.id == data['stage_id'][0]:
                                lines.append(get_xls(obj))

                # ----------------------- FILTER ON DATE AND PARTNER -------------------------
                elif data['filter'] == 'filter_date' and data['filter_partner'] is True:
                    for j in range(0, len(data['partner_name'])):
                        for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                            obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                            if (data['date_from'] <= obj.date_deadline) \
                                    and (data['date_to'] >= obj.date_deadline) \
                                    and obj.partner_id.id == data['partner_name'][j]:
                                lines.append(get_xls(obj))

                # ----------------------- FILTER ON DATE AND STATE -------------------------
                elif data['filter'] == 'filter_date' and data['stage_id'] is not False:
                    for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                        obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                        if (data['date_from'] <= obj.date_deadline) and (data['date_to'] >= obj.date_deadline) \
                                and obj.stage_id.id == data['stage_id'][0]:
                            lines.append(get_xls(obj))

                # ----------------------- FILTER ON PARTNER AND STATE -------------------------
                elif data['stage_id'] is not False and data['filter_partner'] is True:
                    for j in range(0, len(data['partner_name'])):
                        for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                            obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                            if obj.stage_id.id == data['stage_id'][0] and obj.partner_id.id == data['partner_name'][j]:
                                lines.append(get_xls(obj))

                # ----------------------- FILTER ON DATE -------------------------
                elif data['filter'] == 'filter_date':
                    for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                        obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                        if (data['date_from'] <= obj.date_deadline) and (data['date_to'] >= obj.date_deadline):
                            lines.append(get_xls(obj))

                # -----------------------  FILTER ON PARTNER -------------------------
                elif data['filter_partner'] is True:
                    for j in range(0, len(data['partner_name'])):
                        for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                            obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                            if obj.partner_id.id == data['partner_name'][j]:
                                lines.append(get_xls(obj))

                # ----------------------- FILTER ON STATE -------------------------
                elif data['stage_id'] is not False:
                    for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                        obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                        if obj.stage_id.id == data['stage_id'][0]:
                            lines.append(get_xls(obj))

                # ----------------------- NO FILTERS -------------------------
                else:
                    for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                        obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                        lines.append(get_xls(obj))

        return lines


class PrintReport(osv.AbstractModel):
    _name = 'report.car_workshop_report.workshop_pdf'
    _inherit = 'report.abstract_report'
    _template = 'car_workshop_report.workshop_pdf'
    _wrapped_report_class = CarReport
