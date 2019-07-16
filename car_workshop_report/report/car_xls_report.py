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

import xlwt
import datetime
from openerp.addons.report_xls.report_xls import report_xls


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
    templist1 = [(1, 3, 0, 'text', getvals['name']),
                 (2, 3, 0, 'text', getvals['vehicle']),
                 (3, 2, 0, 'text', getvals['date_deadline']),
                 (4, 2, 0, 'text', getvals['partner_id']),
                 (5, 2, 0, 'text', getvals['user_id']),
                 (6, 1, 0, 'number', getvals['amount_total']),
                 (7, 1, 0, 'text',   getvals['stage_id']),
                 ]
    return templist1


class SaleOrderReport(report_xls):

    def generate_xls_report(self, _p, _xs, data, objects, wb):
            report_name = "Car Workshop Report"
            ws = wb.add_sheet(report_name[:31])
            ws.panes_frozen = True
            ws.remove_splits = True
            ws.portrait = 1
            ws.fit_width_to_pages = 1
            row_pos = 0
            ws.set_horz_split_pos(row_pos)
            ws.header_str = self.xls_headers['standard']
            ws.footer_str = self.xls_footers['standard']
            _xs.update({
                'xls_title': 'font: bold true, height 350;'
            })
            _xs.update({
                'xls_sub_title': 'font: bold false, height 250;'
            })
            cell_style = xlwt.easyxf(_xs['xls_title'] + _xs['center'])
            cell_center = xlwt.easyxf(_xs['center'])
            cell_center_bold_no = xlwt.easyxf(_xs['center'] + _xs['bold'])
            cell_left_b = xlwt.easyxf(_xs['left'] + _xs['bold'])
            c_specs = [('report_name', 8, 0, 'text', report_name)]
            row_pos += 1
            row_data = self.xls_row_template(c_specs, ['report_name'])
            row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=cell_style)
            ws.row(row_pos - 1).height_mismatch = True
            ws.row(row_pos - 1).height = 220 * 2
            row_pos += 1
            date_report = "Date Of Report :" + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M %p"))
            top2 = [('entry1', 3, 0, 'text', date_report)]
            row_data = self.xls_row_template(top2, [x[0] for x in top2])
            row_pos = self.xls_write_row(ws, row_pos, row_data, cell_left_b)
            row_pos += 1

            if data['filter'] == 'filter_date':
                filter1 = "Filter By Date:" + 'Date'
                top4 = [(1, 2, 0, 'text', filter1)]

                row_data = self.xls_row_template(top4, [x[0] for x in top4])
                row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center_bold_no)

                date_from = "Date from :" + str(data['date_from'])
                date_to = "Date to :" + str(data['date_to'])
                top6 = [(1, 2, 0, 'text', date_from), ]
                row_data = self.xls_row_template(top6, [x[0] for x in top6])
                row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)
                top6 = [(1, 2, 0, 'text', date_to), ]
                row_data = self.xls_row_template(top6, [x[0] for x in top6])
                row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)
                row_pos += 1

            else:
                filter1 = "Filter By Date:" + 'No filter'
                top4 = [(1, 2, 0, 'text', filter1)]

                row_data = self.xls_row_template(top4, [x[0] for x in top4])
                row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center_bold_no)

            templist = [(1, 3, 0, 'text', 'Task '),
                        (2, 3, 0, 'text', 'Vehicle'),
                        (3, 2, 0, 'text', 'Deadline'),
                        (4, 2, 0, 'text', 'Customer'),
                        (5, 2, 0, 'text', 'Assignrd To'),
                        (6, 1, 0, 'text', 'Total'),
                        (7, 1, 0, 'text', 'Status'), ]
            row_pos += 1
            row_data = self.xls_row_template(templist, [x[0] for x in templist])
            row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center_bold_no)

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
                                                templist1 = get_xls(obj)

                                                row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                                                row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

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

                                                templist2 = get_xls(obj)

                                                row_data = self.xls_row_template(templist2, [x[0] for x in templist2])
                                                row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

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

                                                templist2 = get_xls(obj)

                                                row_data = self.xls_row_template(templist2, [x[0] for x in templist2])
                                                row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

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

                                                templist2 = get_xls(obj)

                                                row_data = self.xls_row_template(templist2, [x[0] for x in templist2])
                                                row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                        # ----------------------- FILTER ON DATE SP-------------------------
                        elif data['filter'] == 'filter_date':
                            for k in range(0, len(data['vehicles'])):
                                for l in range(0, len(data['sales_person'])):
                                    for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                        obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                        if (data['date_from'] <= obj.date_deadline)\
                                                and (data['date_to'] >= obj.date_deadline) \
                                                and obj.vehicle_id.name.id == data['vehicles'][k] \
                                                and obj.user_id.id == data['sales_person'][l]:

                                            templist2 = get_xls(obj)

                                            row_data = self.xls_row_template(templist2, [x[0] for x in templist2])
                                            row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

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

                                                templist3 = get_xls(obj)

                                                row_data = self.xls_row_template(templist3, [x[0] for x in templist3])
                                                row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                        # ----------------------- FILTER ON STATE SP-------------------------
                        elif data['stage_id'] is not False:
                            for k in range(0, len(data['vehicles'])):
                                for l in range(0, len(data['sales_person'])):
                                    for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                        obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                        if obj.stage_id.id == data['stage_id'][0] \
                                                and obj.vehicle_id.name.id == data['vehicles'][k] \
                                                and obj.user_id.id == data['sales_person'][l]:

                                                templist4 = get_xls(obj)

                                                row_data = self.xls_row_template(templist4, [x[0] for x in templist4])
                                                row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                        # ------------------------ FILTER ON SP---------------------------------------
                        else:
                            for k in range(0, len(data['vehicles'])):
                                for l in range(0, len(data['sales_person'])):
                                    for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                        obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                        if obj.user_id.id == data['sales_person'][l] \
                                                and obj.vehicle_id.name.id == data['vehicles'][k]:

                                                templist4 = get_xls(obj)

                                                row_data = self.xls_row_template(templist4, [x[0] for x in templist4])
                                                row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)
                    else:
                        #  ----------------------- FILTER ON DATE PARTNER STATE -------------------------
                        if data['filter'] == 'filter_date' and data['filter_partner'] is True \
                                and data['stage_id'] is not False:
                            for k in range(0, len(data['vehicles'])):
                                for j in range(0, len(data['partner_name'])):
                                    for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                        obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                        if (data['date_from'] <= obj.date_deadline) \
                                                and (data['date_to'] >= obj.date_deadline) \
                                                and obj.partner_id.id == data['partner_name'][j] \
                                                and obj.vehicle_id.name.id == data['vehicles'][k] \
                                                and obj.stage_id.id == data['stage_id'][0]:
                                            templist1 = get_xls(obj)

                                            row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                                            row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

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
                                            templist2 = get_xls(obj)

                                            row_data = self.xls_row_template(templist2, [x[0] for x in templist2])
                                            row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                        # ----------------------- FILTER ON DATE AND STATE -------------------------
                        elif data['filter'] == 'filter_date' and data['stage_id'] is not False:
                            for k in range(0, len(data['vehicles'])):
                                for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                    obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                    if (data['date_from'] <= obj.date_deadline)\
                                            and (data['date_to'] >= obj.date_deadline) \
                                            and obj.vehicle_id.name.id == data['vehicles'][k] \
                                            and obj.stage_id.id == data['stage_id'][0]:
                                        templist2 = get_xls(obj)

                                        row_data = self.xls_row_template(templist2, [x[0] for x in templist2])
                                        row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                        # ----------------------- FILTER ON PARTNER AND STATE -------------------------
                        elif data['stage_id'] is not False and data['filter_partner'] is True:
                            for k in range(0, len(data['vehicles'])):
                                for j in range(0, len(data['partner_name'])):
                                    for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                        obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                        if obj.stage_id.id == data['stage_id'][0] \
                                                and obj.vehicle_id.name.id == data['vehicles'][k] \
                                                and obj.partner_id.id == data['partner_name'][j]:
                                            templist2 = get_xls(obj)

                                            row_data = self.xls_row_template(templist2, [x[0] for x in templist2])
                                            row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                        # ----------------------- FILTER ON DATE -------------------------
                        elif data['filter'] == 'filter_date':
                            for k in range(0, len(data['vehicles'])):
                                for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                    obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                    if (data['date_from'] <= obj.date_deadline)  \
                                            and obj.vehicle_id.name.id == data['vehicles'][k] \
                                            and (data['date_to'] >= obj.date_deadline):
                                        templist2 = get_xls(obj)

                                        row_data = self.xls_row_template(templist2, [x[0] for x in templist2])
                                        row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                        # -----------------------  FILTER ON PARTNER -------------------------
                        elif data['filter_partner'] is True:
                            for k in range(0, len(data['vehicles'])):
                                for j in range(0, len(data['partner_name'])):
                                    for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                        obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                        if obj.partner_id.id == data['partner_name'][j] \
                                                and obj.vehicle_id.name.id == data['vehicles'][k]:
                                            templist3 = get_xls(obj)

                                            row_data = self.xls_row_template(templist3, [x[0] for x in templist3])
                                            row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                        # ----------------------- FILTER ON STATE -------------------------
                        elif data['stage_id'] is not False:

                            for k in range(0, len(data['vehicles'])):
                                for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                    obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                    if obj.stage_id.id == data['stage_id'][0] \
                                            and obj.vehicle_id.name.id == data['vehicles'][k]:
                                        templist4 = get_xls(obj)

                                        row_data = self.xls_row_template(templist4, [x[0] for x in templist4])
                                        row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                        # ----------------------- VEHICLE ONLY -------------------------
                        else:
                            if len(data['vehicles']) == 0:
                                for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                    obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                    templist4 = get_xls(obj)
                                    row_data = self.xls_row_template(templist4, [x[0] for x in templist4])
                                    row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)
                            else:
                                for k in range(0, len(data['vehicles'])):
                                    for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                        obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                        if obj.vehicle_id.name.id == data['vehicles'][k]:
                                            templist4 = get_xls(obj)
                                            row_data = self.xls_row_template(templist4, [x[0] for x in templist4])
                                            row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

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
                                                and obj.partner_id.id == data['partner_name'][j]\
                                                and obj.stage_id.id == data['stage_id'][0] \
                                                and obj.user_id.id == data['sales_person'][l]:
                                            templist1 = get_xls(obj)

                                            row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                                            row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

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
                                            templist2 = get_xls(obj)

                                            row_data = self.xls_row_template(templist2, [x[0] for x in templist2])
                                            row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                        # ----------------------- FILTER ON DATE AND STATE SP-------------------------
                        elif data['filter'] == 'filter_date' and data['stage_id'] is not False:
                            for l in range(0, len(data['sales_person'])):
                                for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                    obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                    if (data['date_from'] <= obj.date_deadline) \
                                            and (data['date_to'] >= obj.date_deadline) \
                                            and obj.stage_id.id == data['stage_id'][0] \
                                            and obj.user_id.id == data['sales_person'][l]:
                                        templist2 = get_xls(obj)

                                        row_data = self.xls_row_template(templist2, [x[0] for x in templist2])
                                        row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                        # ----------------------- FILTER ON PARTNER AND STATE SP-------------------------
                        elif data['stage_id'] is not False and data['filter_partner'] is True:
                            for j in range(0, len(data['partner_name'])):
                                for l in range(0, len(data['sales_person'])):
                                    for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                        obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                        if obj.stage_id.id == data['stage_id'][0] \
                                                and obj.partner_id.id == data['partner_name'][j] \
                                                and obj.user_id.id == data['sales_person'][l]:
                                            templist2 = get_xls(obj)

                                            row_data = self.xls_row_template(templist2, [x[0] for x in templist2])
                                            row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                        # ----------------------- FILTER ON DATE SP-------------------------
                        elif data['filter'] == 'filter_date':
                            for l in range(0, len(data['sales_person'])):
                                for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                    obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                    if (data['date_from'] <= obj.date_deadline) \
                                            and (data['date_to'] >= obj.date_deadline) \
                                            and obj.user_id.id == data['sales_person'][l]:
                                        templist2 = get_xls(obj)

                                        row_data = self.xls_row_template(templist2, [x[0] for x in templist2])
                                        row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                        # -----------------------  FILTER ON PARTNER SP-------------------------
                        elif data['filter_partner'] is True:
                            for j in range(0, len(data['partner_name'])):
                                for l in range(0, len(data['sales_person'])):
                                    for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                        obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                        if obj.partner_id.id == data['partner_name'][j] \
                                                and obj.user_id.id == data['sales_person'][l]:
                                            templist3 = get_xls(obj)

                                            row_data = self.xls_row_template(templist3, [x[0] for x in templist3])
                                            row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                        # ----------------------- FILTER ON STATE SP-------------------------
                        elif data['stage_id'] is not False:
                            for l in range(0, len(data['sales_person'])):
                                for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                    obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                    if obj.stage_id.id == data['stage_id'][0] \
                                            and obj.user_id.id == data['sales_person'][l]:
                                        templist4 = get_xls(obj)

                                        row_data = self.xls_row_template(templist4, [x[0] for x in templist4])
                                        row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                        # ------------------------ FILTER ON SP---------------------------------------
                        else:
                            for l in range(0, len(data['sales_person'])):
                                for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                    obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                    if obj.user_id.id == data['sales_person'][l]:
                                        templist4 = get_xls(obj)

                                        row_data = self.xls_row_template(templist4, [x[0] for x in templist4])
                                        row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)
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
                                    templist1 = get_xls(obj)

                                    row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                                    row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                    # ----------------------- FILTER ON DATE AND PARTNER -------------------------
                    elif data['filter'] == 'filter_date' and data['filter_partner'] is True:
                        for j in range(0, len(data['partner_name'])):
                            for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                if (data['date_from'] <= obj.date_deadline) \
                                        and (data['date_to'] >= obj.date_deadline) \
                                        and obj.partner_id.id == data['partner_name'][j]:
                                    templist2 = get_xls(obj)

                                    row_data = self.xls_row_template(templist2, [x[0] for x in templist2])
                                    row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                    # ----------------------- FILTER ON DATE AND STATE -------------------------
                    elif data['filter'] == 'filter_date' and data['stage_id'] is not False:
                        for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                            obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                            if (data['date_from'] <= obj.date_deadline) and (data['date_to'] >= obj.date_deadline) \
                                    and obj.stage_id.id == data['stage_id'][0]:
                                templist2 = get_xls(obj)

                                row_data = self.xls_row_template(templist2, [x[0] for x in templist2])
                                row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                    # ----------------------- FILTER ON PARTNER AND STATE -------------------------
                    elif data['stage_id'] is not False and data['filter_partner'] is True:
                        for j in range(0, len(data['partner_name'])):
                            for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                if obj.stage_id.id == data['stage_id'][0] \
                                        and obj.partner_id.id == data['partner_name'][j]:
                                    templist2 = get_xls(obj)

                                    row_data = self.xls_row_template(templist2, [x[0] for x in templist2])
                                    row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                    # ----------------------- FILTER ON DATE -------------------------
                    elif data['filter'] == 'filter_date':
                        for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                            obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                            if (data['date_from'] <= obj.date_deadline) and (data['date_to'] >= obj.date_deadline):
                                templist2 = get_xls(obj)

                                row_data = self.xls_row_template(templist2, [x[0] for x in templist2])
                                row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                    # -----------------------  FILTER ON PARTNER -------------------------
                    elif data['filter_partner'] is True:
                        for j in range(0, len(data['partner_name'])):
                            for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                                obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                                if obj.partner_id.id == data['partner_name'][j]:
                                    templist3 = get_xls(obj)

                                    row_data = self.xls_row_template(templist3, [x[0] for x in templist3])
                                    row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                    # ----------------------- FILTER ON STATE -------------------------
                    elif data['stage_id'] is not False:
                        for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                            obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                            if obj.stage_id.id == data['stage_id'][0]:
                                templist4 = get_xls(obj)

                                row_data = self.xls_row_template(templist4, [x[0] for x in templist4])
                                row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                    # ----------------------- NO FILTERS -------------------------
                    else:
                        for i in self.pool.get('car.workshop').search(self.cr, self.uid, []):
                            obj = self.pool.get('car.workshop').browse(self.cr, self.uid, i)
                            templist4 = get_xls(obj)
                            row_data = self.xls_row_template(templist4, [x[0] for x in templist4])
                            row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

SaleOrderReport('report.workshop_report', 'car.workshop')
