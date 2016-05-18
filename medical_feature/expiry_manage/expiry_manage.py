from openerp import models, fields, _
from openerp import api
import datetime
from dateutil import parser


class StockTransferDetailsItems(models.TransientModel):
    _inherit = 'stock.transfer_details_items'

    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number')

    @api.onchange('lot_id')
    def when_items_changes_(self):
        # ALERT DATE [alert_date]
        if self.lot_id.alert_date is not False and parser.parse(self.lot_id.alert_date) < datetime.datetime.now():
            return {'warning': {'title': _('Warning'), 'message': _('The lot  \''+self.lot_id.name+'\' of '+' medicine \''+self.lot_id.product_id.name+'\'\n must not be consumed and should be removed from the stock.')}}
        # REMOVAL DATE [removal_date]
        if self.lot_id.removal_date is not False and parser.parse(self.lot_id.removal_date) < datetime.datetime.now():
            return {'warning': {'title': _('Warning'), 'message': _('The lot  \''+self.lot_id.name+'\' of '+' medicine \''+self.lot_id.product_id.name+'\'\n must not be consumed and should be removed from the stock.')}}
        # END OF LIFE DATE [life_date]
        if self.lot_id.life_date is not False and parser.parse(self.lot_id.life_date) < datetime.datetime.now():
            return {'warning': {'title': _('Warning'), 'message': _('The lot  \''+self.lot_id.name+'\' of '+' medicine \''+self.lot_id.product_id.name+'\'\n is dangerous and must not be consumed.')}}
        # BEST BEFORE DATE [use_date]
        if self.lot_id.use_date is not False and parser.parse(self.lot_id.use_date) < datetime.datetime.now():
            return {'warning': {'title': _('Warning'), 'message': _('The lot  \''+self.lot_id.name+'\' of '+' medicine \''+self.lot_id.product_id.name+'\'\n is not good for use now.')}}


class AddColorSerialNo(models.Model):
    _inherit = 'stock.production.lot'

    def _get_default_vals(self):
        for each_lots in self:
            if each_lots.alert_date is not False and parser.parse(each_lots.alert_date) < datetime.datetime.now():
                each_lots.state = 'red'
            elif each_lots.removal_date is not False and parser.parse(each_lots.removal_date) < datetime.datetime.now():
                each_lots.state = 'red'
            elif each_lots.life_date is not False and parser.parse(each_lots.life_date) < datetime.datetime.now():
                each_lots.state = 'red'
            elif each_lots.use_date is not False and parser.parse(each_lots.use_date) < datetime.datetime.now():
                each_lots.state = 'lite_red'
            else:
                each_lots.state = 'normal'


    state = fields.Selection([('normal', 'Normal'),
                              ('lite_red', 'Not Good'),
                              ('red', 'To Be Removed')],
                             string='Status',
                             compute=lambda self: self._get_default_vals()
                             # default=lambda self: self._get_default_vals()
                             )

