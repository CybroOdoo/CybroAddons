# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.report import report_sxw
from openerp.osv import osv


class FleetParser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(FleetParser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'contract_details': self.contract_details,
            'cost_details': self.cost_details,
            'odoometer_details': self.odoometer_details,
            # 'service_details': self.service_details,

        })
        self.context = context

    def contract_details(self, d):
        contract = []

        obj_contract = self.pool.get('fleet.vehicle.log.contract').search(self.cr, self.uid, [('vehicle_id', '=', d)])
        if obj_contract:
            for obj in obj_contract:
                obj_cont = self.pool.get('fleet.vehicle.log.contract').browse(self.cr, self.uid, obj, context=None)
                vals = {
                    'vendor': obj_cont.insurer_id.name,
                    'date': obj_cont.start_date,
                    'date_closed': obj_cont.expiration_date,
                    'state': obj_cont.state,
                    'type':obj_cont.cost_subtype_id.name,

                }
                contract.append(vals)
            return contract

    def cost_details(self, d):
        contract = []

        obj_contract = self.pool.get('fleet.vehicle.cost').search(self.cr, self.uid,
                                                                          [('vehicle_id', '=', d)])
        if obj_contract:
            for obj in obj_contract:
                obj_cont = self.pool.get('fleet.vehicle.cost').browse(self.cr, self.uid, obj, context=None)
                vals = {
                    'price': obj_cont.amount,
                    'type': obj_cont.cost_subtype_id.name,
                    'date': obj_cont.date,


                }
                contract.append(vals)
            return contract

    def odoometer_details(self, d):
        contract = []

        obj_contract = self.pool.get('fleet.vehicle.odometer').search(self.cr, self.uid,
                                                                  [('vehicle_id', '=', d)])
        if obj_contract:
            for obj in obj_contract:
                obj_cont = self.pool.get('fleet.vehicle.odometer').browse(self.cr, self.uid, obj, context=None)
                vals = {
                    'date': obj_cont.date,
                    'value': obj_cont.value,
                    'unit': obj_cont.unit,

                }
                contract.append(vals)
            return contract
    #
    # def service_details(self, d):
    #     contract = []
    #
    #     obj_contract = self.pool.get('fleet.vehicle.log.services').search(self.cr, self.uid,
    #                                                                   [('vehicle_id', '=', d)])
    #     if obj_contract:
    #         for obj in obj_contract:
    #             obj_cont = self.pool.get('fleet.vehicle.log.services').browse(self.cr, self.uid, obj, context=None)
    #             vals = {
    #                 'type': obj_cont.cost_subtype_id.name,
    #                 'value': obj_cont.value,
    #                 'unit': obj_cont.unit,
    #
    #             }
    #             contract.append(vals)
    #
    #         return contract


class PrintReport(osv.AbstractModel):
    _name = 'report.fleet_report.report_fleet'
    _inherit = 'report.abstract_report'
    _template = 'fleet_report.report_fleet'
    _wrapped_report_class = FleetParser
