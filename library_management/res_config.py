# -*- coding: utf-8 -*-
from openerp import SUPERUSER_ID
from openerp.tools.translate import _
from openerp.osv import fields, osv


class PropertyConfigSettings(osv.TransientModel):
    _name = 'library.config.settings'
    _inherit = 'res.config.settings'

    def _default_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id.id

    _columns = {
        'store': fields.many2one('stock.warehouse', _('Library Store'), help=_('Account used for Library Configuration')),
        'account_id': fields.many2one('account.account', _('Library Account'),
                                      domain="[('type', '=', 'receivable')]",
                                      help=_('Account used for Library Configuration')),
        'fine_per_day': fields.float(_('Fine per day')),

    }

    def get_default_store(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        store = ir_values.get_default(cr, uid, 'library.config.settings', 'store')
        return {
            'store': store,
        }

    def set_store(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        wizard = self.browse(cr, uid, ids)[0]
        if wizard.store:
            store = wizard.store
            ir_values.set_default(cr, SUPERUSER_ID, 'library.config.settings', 'store', store.id)
        else:
            store = False
            ir_values.set_default(cr, SUPERUSER_ID, 'library.config.settings', 'store', store)

    def get_default_account_id(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        account_id = ir_values.get_default(cr, uid, 'library.config.settings', 'account_id')
        return {
            'store': account_id,
        }

    def set_account_id(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        wizard = self.browse(cr, uid, ids)[0]
        if wizard.account_id:
            account_id = wizard.account_id
            ir_values.set_default(cr, SUPERUSER_ID, 'library.config.settings', 'account_id', account_id.id)
        else:
            account_id = False
            ir_values.set_default(cr, SUPERUSER_ID, 'library.config.settings', 'account_id', account_id)

    def get_default_fine_per_day(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        fine_per_day = ir_values.get_default(cr, uid, 'library.config.settings', 'fine_per_day')
        return {
            'store': fine_per_day,
        }

    def set_fine_per_day(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        wizard = self.browse(cr, uid, ids)[0]
        if wizard.fine_per_day:
            fine_per_day = wizard.fine_per_day
            ir_values.set_default(cr, SUPERUSER_ID, 'library.config.settings', 'fine_per_day', fine_per_day)
        else:
           fine_per_day = 0.0
           ir_values.set_default(cr, SUPERUSER_ID, 'library.config.settings', 'store',fine_per_day)