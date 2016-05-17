from openerp import models, fields,api,http,SUPERUSER_ID


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    type = fields.Selection([('consu', 'Consumable'),
                             ('service', 'Service')],
                            'Product Type',
                            required=True,
                            help="Consumable are product where you don't manage stock, a service is a non-material product provided by a company or an individual.",
                            default='service')


class SaleAdvancePaymentInv(models.Model):
    _inherit = "sale.advance.payment.inv"

    advance_payment_method =fields.Selection(
            [('all', 'Invoice the whole Booking'), ('percentage','Percentage'), ('fixed','Fixed price (deposit)'),
                ('lines', 'Some Booking lines')],
            'What do you want to invoice?', required=True,
            help="""Use Invoice the whole sale order to create the final invoice.
                Use Percentage to invoice a percentage of the total amount.
                Use Fixed Price to invoice a specific amound in advance.
                Use Some Order Lines to invoice a selection of the sales order lines.""")