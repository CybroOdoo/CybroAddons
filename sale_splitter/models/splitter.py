
from openerp import fields, models, api


class config_bool(models.Model):
    _inherit = 'sale.config.settings'

    conf_bool = fields.Boolean(string="Enables Sale order splitting")


class wizard(models.TransientModel):
    _name = 'split.button.wiz'
    temp = 1

    line_count = fields.Char('Divide By', required=True)

    @api.one
    def confirm_split(self,vals):
        line_ids = []
        so_create = []
        so_id = vals['active_id']
        sale_obj = self.pool.get('sale.order').browse(self._cr, self._uid, so_id)
        countt= 0
        for lines in sale_obj.order_line:
            create_obt = {
                'product_id': lines.product_id.id,
                'name': lines.name,
                'product_uom_qty': lines.product_uom_qty,
                'price_unit': lines.price_unit,
                'tax_id': lines.tax_id,
                'product_uom': lines.product_uom.id,
                'price_subtotal': lines.price_subtotal
            }
            so_create.append((0, 0, create_obt))
            line_ids.append({'ids': lines.id})
            if len(line_ids) == int(self.line_count):
                countt = countt + 1
                self.pool.get('sale.order').create(self._cr, self._uid, {
                    'name': sale_obj.name + '/00' + str(countt),
                    'partner_id': sale_obj.partner_id.id,
                    'validity_date': sale_obj.validity_date,
                    'order_line': so_create,
                    'pricelist_id': sale_obj.pricelist_id.id
                })
                so_create = []
                for idss in line_ids:
                    self._cr.execute("delete  from sale_order_line where id = %s", [idss['ids']])
                line_ids = []
                self.temp = 0


            self.temp += 1
        counted=0
        for i in sale_obj.order_line:
            counted += 1
        if counted == 0:
                self._cr.execute("delete from sale_order where id = %s", [sale_obj.id])
        else:
            untaxed_total = 0.0
            tax = 0.0
            for line in sale_obj.order_line:
                untaxed_total += line.price_subtotal
                tax += line.price_tax

            sale_obj.amount_untaxed = sale_obj.pricelist_id.currency_id.round(untaxed_total)
            sale_obj.amount_tax = sale_obj.pricelist_id.currency_id.round(tax)
            sale_obj.amount_total = sale_obj.amount_untaxed + sale_obj.amount_tax


class button_split(models.Model):

    _inherit = 'sale.order'


    parent_id = fields.Char()

    def button_split(self, cr, uid, ids, context=None):
       return {
        'name': 'Confirm Split',

        'type': 'ir.actions.act_window',

        'view_mode': 'form',

        'res_model': 'split.button.wiz',

        'target': 'new',

        'vals': self.pool.get('sale.order').browse(cr, uid, ids).id

       }
