# -*- coding: utf-8 -*-
from openerp.osv import fields, osv


class SettingOption(osv.osv_memory):
    _inherit = 'hr.config.settings'
    _columns = {
        'visa_validity': fields.boolean("Get email notification on employee VISA expiration",
                                        help="""Allow to define from how many days before to start alert
                                        Employee and other configured addresses will get the notification emails each day."""),
        'limit_amount': fields.integer("from", size=10)
        }

    def get_default_visa_details(self, cr, uid, fields, context=None):
        ir_values = self.pool.get('ir.values')
        visa_validity = ir_values.get_default(cr, uid, 'sale.config.settings', 'visa_validity')
        limit_amount = ir_values.get_default(cr, uid, 'sale.config.settings', 'limit_amount')
        return {'visa_validity': visa_validity, 'limit_amount': limit_amount}
