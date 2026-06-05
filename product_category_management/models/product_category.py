# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ProductCategory(models.Model):
    """Extend product.category with description, image, product count, and hierarchy HTML."""
    _inherit = 'product.category'

    description = fields.Text(string='Description', help="A description of the product category.")
    image = fields.Binary(string='Image', help="This field holds the image used as image for the product, limited to 1024x1024px.")
    product_count = fields.Integer(string='Product Count', compute='_compute_product_count', help="The number of products under this category")
    active = fields.Boolean(
        default=True,
        help="If unchecked, it will allow you to hide the "
        "product category without removing it.",
    )
    category_hierarchy_html = fields.Html(
        string='Category Hierarchy',
        compute='_compute_category_hierarchy_html',
        sanitize=False
    )

    @api.constrains("active")
    def _check_archive(self):
        """Prevent archiving categories that have products or child categories with products."""
        to_archive = self.filtered(lambda r: not r.active)
        if (
            self.env["product.template"]
            .with_context(active_test=False)
            .search([("categ_id", "child_of", to_archive.ids)])
        ):
            raise ValidationError(
                _(
                    "At least one category that you are trying to archive or one "
                    "of its children has one or more product linked to it."
                )
            )

    def _compute_product_count(self):
        """Compute the number of products in each category."""
        for category in self:
            category.product_count = self.env['product.template'].search_count([('categ_id', '=', category.id)])

    def _build_hierarchy_html(self, category):
        """Build HTML representation of a category and its children recursively."""
        return f"""
            <li class="category-node">
                <div class="node-box">
                    <i class="fa fa-folder-open icon-folder"></i>
                    <span class="category-name">{category.name}</span>
                    <span class="badge">{category.product_count} product{'s' if category.product_count != 1 else ''}</span>
                </div>
                {'<ul class="category-children">' + ''.join(self._build_hierarchy_html(child) for child in category.child_id) + '</ul>' if category.child_id else ''}
            </li>
        """

    @api.depends('child_id')
    def _compute_category_hierarchy_html(self):
        """Compute HTML for the full category hierarchy with styling."""
        for rec in self:
            rec._compute_product_count()
            style = """
            <style>
                .category-tree {
                    font-family: "Segoe UI", Roboto, sans-serif;
                    color: #333;
                    padding: 10px;
                    background: #fafafa;
                    border-radius: 8px;
                    border: 1px solid #e2e2e2;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                }
                .category-tree ul {
                    list-style: none;
                    padding-left: 20px;
                    position: relative;
                }
                .category-tree ul::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 10px;
                    width: 1px;
                    height: 100%;
                    background: #ccc;
                }
                .category-tree li {
                    margin: 12px 0;
                    position: relative;
                }
                .category-tree li::before {
                    content: '';
                    position: absolute;
                    top: 12px;
                    left: -10px;
                    width: 20px;
                    height: 1px;
                    background: #ccc;
                }
                .node-box {
                    background: white;
                    border: 1px solid #dcdcdc;
                    border-radius: 6px;
                    padding: 8px 12px;
                    display: inline-flex;
                    align-items: center;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                    transition: 0.2s;
                }
                .node-box:hover {
                    background: #f0f8ff;
                    border-color: #007bff;
                }
                .icon-folder {
                    color: #007bff;
                    margin-right: 8px;
                }
                .category-name {
                    font-weight: 600;
                    margin-right: 8px;
                }
                .badge {
                    background-color: #17a2b8;
                    color: #fff;
                    font-size: 11px;
                    padding: 2px 8px;
                    border-radius: 10px;
                }
            </style>
            """

            # Include self in the hierarchy
            root_html = f"<ul class='category-root'>{rec._build_hierarchy_html(rec)}</ul>"
            rec.category_hierarchy_html = f"<div class='category-tree'>{style}{root_html}</div>"
