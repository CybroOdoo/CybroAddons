from openerp import fields, models


class IrActionsReportXml(models.Model):
    _inherit = 'ir.actions.report.xml'

    report_type = fields.Selection(selection_add=[("xlsx", "xlsx")])
