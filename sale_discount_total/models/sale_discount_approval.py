from openerp import api, models, fields
from openerp.osv import fields, osv
from openerp import SUPERUSER_ID

##############################################################sale settings##############################################################

class Sale_config_settings(osv.TransientModel):
    _inherit = 'sale.config.settings'
    _columns = {
        'limit_discount': fields.integer('Discount limit requires approval %', required=True,
                                         help="Discount after which approval of sale is required."),
        'module_sale_discount_approval': fields.boolean("Force two levels of approvals",
                                                        help='Provide a double validation mechanism for sale exceeding minimum discount.\n'
                                                        ),
    }

    _defaults = {
        'limit_discount': 40,
    }

    def get_default_limit_discount(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        limit_discount = ir_values.get_default(cr, uid, 'sale.config.settings', 'limit_discount')
        return {
            'limit_discount': limit_discount,
        }

    def set_limit_discount(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        wizard = self.browse(cr, uid, ids)[0]
        if wizard.limit_discount:
            limit_discount = wizard.limit_discount
            ir_values.set_default(cr, SUPERUSER_ID, 'sale.config.settings', 'limit_discount', limit_discount)

    def get_default_module_sale_discount_approval(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        module_sale_discount_approval = ir_values.get_default(cr, uid, 'sale.config.settings',
                                                              'module_sale_discount_approval')
        return {
            'module_sale_discount_approval': module_sale_discount_approval == 'True',
        }

    def set_module_sale_discount_approval(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        wizard = self.browse(cr, uid, ids)[0]
        if wizard.module_sale_discount_approval:
            module_sale_discount_approval = 'True'
        else:
            module_sale_discount_approval = 'False'

        ir_values.set_default(cr, SUPERUSER_ID, 'sale.config.settings', 'module_sale_discount_approval',
                              module_sale_discount_approval)


#######################################################sale order workflow##############################################################

class SaleInherit(osv.Model):
    _inherit = 'sale.order'

    _columns = {
        'state': fields.selection([('draft', 'Draft Quotation'),
                                   ('sent', 'Quotation Sent'),
                                   ('cancel', 'Cancelled'),
                                   ('waiting_date', 'Waiting Schedule'),
                                   ('waitingapproval', 'Waiting Approval'),
                                   ('progress', 'Sales Order'),
                                   ('manual', 'Sale to Invoice'),
                                   ('shipping_except', 'Shipping Exception'),
                                   ('invoice_except', 'Invoice Exception'),
                                   ('done', 'Done')], required=True, track_visibility='onchange'),
    }

    def action_button_confirm(self, cr, uid, ids, context=None):
        discnt = 0.0
        no_line = 0.0
        line_dicnt = 0.0
        prod_price = 0.0
        conf = self.pool.get('ir.values')
        sale_obj = self.browse(cr, uid, ids, context)
        double_valid = conf.get_default(cr, uid, 'sale.config.settings', 'module_sale_discount_approval')
        if double_valid == 'True':
            min_disct = conf.get_default(cr, uid, 'sale.config.settings', 'limit_discount')
            for line in sale_obj.order_line:
                no_line += 1
                discnt += line.discount
            discnt = (discnt / no_line)
            if discnt >= min_disct:
                assert len(ids) == 1, 'This option should only be used for a single id at a time.'
                self.signal_workflow(cr, uid, ids, 'order_toapprov')
                return True
            else:
                return super(SaleInherit, self).action_button_confirm(cr, uid, ids, context)
        else:
            return super(SaleInherit, self).action_button_confirm(cr, uid, ids, context)

        ####################################### workflow functions#############################################################################

    @api.one
    def wait_approval(self):

        self.state = 'waitingapproval'
        return True
