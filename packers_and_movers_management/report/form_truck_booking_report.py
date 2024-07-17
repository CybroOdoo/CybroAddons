# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
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
from odoo import api, models


class TruckFormReport(models.AbstractModel):
    """Class is used to print pdf report for the truck_booking module form
    view"""
    _name = 'report.packers_and_movers_management.form_truck_booking_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Function to return values for the report,
        docids: it will provide the current id the model"""
        query = """select tb.reference_no,pr.name,fv.name as truck,gt.name as goods,tb.from_location,tb.to_location,
                tb.distance,tb.weight,tb.unit,amount,tb.date,tb.state from truck_booking as tb
                inner join res_partner as pr on pr.id = tb.partner_id
                inner join fleet_vehicle_model as fv on fv.id = tb.truck_id
                inner join goods_type as gt on gt.id = tb.goods_type_id
                where tb.id = %d""" % docids
        self.env.cr.execute(query)
        report = self.env.cr.dictfetchall()
        return {'doc_ids': docids, 'report': report}
