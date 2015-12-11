from openerp import models
from openerp.report import report_sxw
from datetime import date
class report_lib(report_sxw.rml_parse):
    _name = 'report.library_management.report_invoice_library'
    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(report_lib, self).__init__(cr, uid, name, context = context)
        self.localcontext.update({
            'timee':self._timee,
            'get_data': self._get_data,

        })
    def _timee(self,data):
        date_now=date.today().strftime('%Y-%m-%d')
        return date_now

    def _get_data(self,issue_code):
        acc_obj=self.pool.get('account.invoice.line')
        search = acc_obj.search(self.cr,self.uid,[('name', '=', issue_code)])
        var = acc_obj.browse(self.cr, self.uid, search)
        descri = var.name
        product = var.product_id
        quant = var.quantity
        price = var.price_unit
        subtotal = var.price_subtotal
        return {'descri': descri, 'product': product.name,'quant': quant,'price': price,'subtotal': subtotal}

class report_lib_invoice(models.AbstractModel):
    _name = 'report.library_management.report_invoice_library'
    _inherit = 'report.abstract_report'
    _template = 'library_management.report_invoice_library'
    _wrapped_report_class = report_lib