# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Paid App Development Team (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class WebsiteCustomerPortal(CustomerPortal):
    """ Functon : Prepare portal values, datas are searched from document.file
        :return document count, request count
    """
    def _prepare_home_portal_values(self, counters):
        """Functon : Prepare portal values,
            datas are searched from document.file"""
        values = super(
            WebsiteCustomerPortal, self)._prepare_home_portal_values(counters)
        if 'document_count' in counters:
            values['document_count'] = request.env[
                'document.file'].sudo().search_count([
                    ('user_id.id', '=', request.uid)
                ])
            values['request_count'] = request.env[
                'request.document'].sudo().search_count([
                    ('user_id.id', '=', request.uid),
                    ('state', '=', 'requested')
                ])
        return values
