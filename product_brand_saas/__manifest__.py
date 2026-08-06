###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sreeraj M (odoo@cybrosys.com)
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
################################################################################
{
    'name': 'Product Brand Management for Odoo online (SaaS 19.4)',
    'version': 'saas~19.4.1.0.0',
    'category': 'Services',
    'summary': """Brand for Odoo Online, Product Brand for Odoo Online, Band Management, Odoo Online Custom Modules""",
    'description': """
    Product Brand Management
for Odoo Online helps businesses organize and manage product brands efficiently.
The module provides dedicated Brand, Brand Category, and Brand Tag management, along with enhanced product organization,
search, filtering, reporting, and dashboard capabilities.It is designed for Odoo Online (SaaS) and includes
Studio-based customizations for a seamless and user-friendly experience.
""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['product',
                'web_studio'],
    'data': ['data/ir_model.xml',
             'data/ir_model_fields.xml',
             'data/ir_actions_act_window.xml',
             'data/ir_actions_report.xml',
             'data/ir_ui_menu.xml',
             'data/ir_access.xml',
             'data/ir_default.xml',
             'data/ir_ui_view.xml'],
    'demo': ['demo/res_partner.xml',
             'demo/x_brands_stage.xml'],
    'assets': {
        'web.assets_backend': [
            'product_brand_saas/static/src/js/brand_dashboard.js',
            'product_brand_saas/static/src/xml/brand_dashboard.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'application': True,
    'installable': True,
}
