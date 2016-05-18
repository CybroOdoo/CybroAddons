from openerp import models, fields,_
from openerp import api


# ROUTE
class DistributionRoutes(models.Model):
    _name = 'pharmacy_management.route'

    name = fields.Char('Route Name')
    route_code = fields.Char()
    distributor = fields.Many2one('res.users', 'Distributor')
    customer_list = fields.One2many('res.partner', 'customer_route')

    @api.one
    def _get_customer_count(self):
        self.count_customers = len(self.customer_list)
    count_customers = fields.Integer(compute='_get_customer_count')
    # location_list = fields.One2many('pharmacy_management.route.location', 'route_id')
    location_list1 = fields.Many2many('pharmacy_management.route.location', 'route_id', string='Locations')

    def locations_btn(self, cr, uid, ids, context=None):
        return {
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'pharmacy_management.route.location',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name' : _('All Route Locations'),
                }


# RETAILERS
class RouteInCustomer(models.Model):
    _inherit = 'res.partner'

    @api.onchange('customer_route')
    def set_id_of_route_distributor(self):
        print self.customer_route.distributor.id
        self.id_of_route_distributor = self.customer_route.distributor.id

    customer_route = fields.Many2one('pharmacy_management.route', 'Route')
    id_of_route_distributor = fields.Integer()


# SALE ORDER
class RouteInSaleOrder(models.Model):
    _inherit = 'sale.order'

    route_of_customer = fields.Many2one('pharmacy_management.route', 'Route of Customer')

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        if not part:
            return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False,  'payment_term': False, 'fiscal_position': False}}

        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        addr = self.pool.get('res.partner').address_get(cr, uid, [part.id], ['delivery', 'invoice', 'contact'])
        pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False
        invoice_part = self.pool.get('res.partner').browse(cr, uid, addr['invoice'], context=context)
        payment_term = invoice_part.property_payment_term and invoice_part.property_payment_term.id or False
        dedicated_salesman = part.user_id and part.user_id.id or uid
        val = {
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'payment_term': payment_term,
            'user_id': dedicated_salesman,
        }
        delivery_onchange = self.onchange_delivery_id(cr, uid, ids, False, part.id, addr['delivery'], False,  context=context)
        val.update(delivery_onchange['value'])
        if pricelist:
            val['pricelist_id'] = pricelist
        if not self._get_default_section_id(cr, uid, context=context) and part.section_id:
            val['section_id'] = part.section_id.id
        sale_note = self.get_salenote(cr, uid, ids, part.id, context=context)
        if sale_note: val.update({'note': sale_note})
        # =================================================
        val['route_of_customer'] = part.customer_route.id
        # val['user_id'] = part.customer_route.distributor.id
        return {'value': val}

    def _get_route_of_customer_to_show(self):
        self.route_of_customer_to_show = self.partner_id.customer_route.id
    route_of_customer_to_show = fields.Many2one('pharmacy_management.route', 'Route of Customer' , compute='_get_route_of_customer_to_show')


class Locations(models.Model):
    _name = 'pharmacy_management.route.location'

    name = fields.Char('Location Name')
    route_id = fields.Many2one('pharmacy_management.route')