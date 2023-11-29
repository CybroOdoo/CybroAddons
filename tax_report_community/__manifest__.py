# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Muhammed Dilshad Tk (odoo@cybrosys.com)
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
{
    "name": "Tax Report",
    "summary": """ Tax Report for odoo 16""",
    "version": "16.0.1.0.0",
    "description": """This module will generate tax report in excel and pdf""",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "website": "https://cybrosys.com",
    "category": "Accounting",
    "depends": ["base_accounting_kit", "account"],
    "data": ["views/account_report_tax_views.xml"],
    "assets": {
        "web.assets_backend": [
            "tax_report_community/static/src/js/action_manager.js",
        ],
    },
    "license": "OPL-1",
    "images": ["static/description/banner.png"],
    "installable": True,
    "auto_install": False,
    "application": False,
}
