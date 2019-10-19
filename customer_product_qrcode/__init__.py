# -*- coding: utf-8 -*-
from . import models
from . import report
from odoo import api, SUPERUSER_ID


def _set_qr(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for record in env['product.product'].search([]):
        name = record.name.replace(" ", "")
        record.sequence = 'DEF' + name.upper()+str(record.id)
        record.generate_qr()