# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2012-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Cybrosys Technologies(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
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
        'product': obj.product_id.name,
        'product_qty': obj.product_qty,
        'product_uom': obj.product_uom.name,
        'user_id': obj.user_id.name,
        'date_planned': obj.date_planned,
        'state': obj.state,
    }
    templist1 = [(1, 3, 0, 'text', getvals['name']),
                 (2, 3, 0, 'text', getvals['product']),
                 (3, 2, 0, 'text', getvals['product_qty']),
                 (4, 2, 0, 'text', getvals['product_uom']),
                 (5, 2, 0, 'text', getvals['user_id']),
                 (6, 1, 0, 'text', getvals['date_planned']),
                 (7, 1, 0, 'text',   getvals['state']),
                 ]
    return templist1


class MrpXlsReport(report_xls):

    def generate_xls_report(self, _p, _xs, data, objects, wb):
            report_name = "Manufacturing Orders"
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

            templist = [(1, 3, 0, 'text', 'Reference'),
                        (2, 3, 0, 'text', 'Product'),
                        (3, 2, 0, 'text', 'Quantity'),
                        (4, 2, 0, 'text', 'Unit'),
                        (5, 2, 0, 'text', 'Responsible'),
                        (6, 1, 0, 'text', 'Start Date'),
                        (7, 1, 0, 'text', 'State'), ]
            row_pos += 1
            row_data = self.xls_row_template(templist, [x[0] for x in templist])
            row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center_bold_no)

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
                                        templist1 = get_xls(obj)

                                        row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                                        row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                    elif len(data['product']) == 0 and data['stage'] is not False:
                        for l in range(0, len(data['responsible'])):
                            for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                                obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                                if (data['date_from'] <= obj.date_planned) \
                                        and (data['date_to'] >= obj.date_planned) \
                                        and obj.state == data['stage'] \
                                        and obj.user_id.id == data['responsible'][l]:
                                    templist1 = get_xls(obj)

                                    row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                                    row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

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
                                        templist1 = get_xls(obj)

                                        row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                                        row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                    if len(data['product']) == 0 \
                            and data['stage'] is False:
                        for l in range(0, len(data['responsible'])):
                            for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                                obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                                if (data['date_from'] <= obj.date_planned) \
                                        and (data['date_to'] >= obj.date_planned) \
                                        and obj.user_id.id == data['responsible'][l]:
                                    templist1 = get_xls(obj)

                                    row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                                    row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

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
                                    templist1 = get_xls(obj)

                                    row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                                    row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                    elif len(data['product']) == 0 and data['stage'] is not False:
                        for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                            obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                            if (data['date_from'] <= obj.date_planned) \
                                    and (data['date_to'] >= obj.date_planned) \
                                    and obj.state == data['stage']:
                                templist1 = get_xls(obj)

                                row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                                row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                    if len(data['product']) > 0 \
                            and data['stage'] is False:
                        for k in range(0, len(data['product'])):
                            for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                                obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                                if (data['date_from'] <= obj.date_planned) \
                                        and (data['date_to'] >= obj.date_planned) \
                                        and obj.product_id.id == data['product'][k]:
                                    templist1 = get_xls(obj)

                                    row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                                    row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                    if len(data['product']) == 0 \
                            and data['stage'] is False:
                        for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                            obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                            if (data['date_from'] <= obj.date_planned) \
                                    and (data['date_to'] >= obj.date_planned):
                                templist1 = get_xls(obj)

                                row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                                row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

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
                                        templist1 = get_xls(obj)

                                        row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                                        row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                    elif len(data['product']) == 0 and data['stage'] is not False:
                        for l in range(0, len(data['responsible'])):
                            for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                                obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                                if obj.state == data['stage'] \
                                        and obj.user_id.id == data['responsible'][l]:
                                    templist1 = get_xls(obj)

                                    row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                                    row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                    if len(data['product']) > 0 \
                            and data['stage'] is False:
                        for k in range(0, len(data['product'])):
                            for l in range(0, len(data['responsible'])):
                                for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                                    obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                                    if obj.product_id.id == data['product'][k] \
                                            and obj.user_id.id == data['responsible'][l]:
                                        templist1 = get_xls(obj)

                                        row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                                        row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                    if len(data['product']) == 0 \
                            and data['stage'] is False:
                        for l in range(0, len(data['responsible'])):
                            for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                                obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                                if obj.user_id.id == data['responsible'][l]:
                                    templist1 = get_xls(obj)

                                    row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                                    row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                if data['filter_user'] is False:

                    if len(data['product']) > 0 \
                            and data['stage'] is not False:
                        for k in range(0, len(data['product'])):
                            for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                                obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                                if obj.state == data['stage'] \
                                        and obj.product_id.id == data['product'][k]:
                                    templist1 = get_xls(obj)

                                    row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                                    row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                    elif len(data['product']) == 0 and data['stage'] is not False:
                        for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                            obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                            if obj.state == data['stage']:
                                templist1 = get_xls(obj)

                                row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                                row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                    if len(data['product']) > 0 \
                            and data['stage'] is False:
                        for k in range(0, len(data['product'])):
                            for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                                obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                                if obj.product_id.id == data['product'][k]:
                                    templist1 = get_xls(obj)

                                    row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                                    row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

                    if len(data['product']) == 0 \
                            and data['stage'] is False:
                        for i in self.pool.get('mrp.production').search(self.cr, self.uid, []):
                            obj = self.pool.get('mrp.production').browse(self.cr, self.uid, i)
                            templist1 = get_xls(obj)

                            row_data = self.xls_row_template(templist1, [x[0] for x in templist1])
                            row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)

MrpXlsReport('report.mrp_reports_xls', 'mrp.production')
