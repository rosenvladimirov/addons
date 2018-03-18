# coding: utf-8
# Copyright (C) 2016-Today: La Louve (<http://www.lalouve.net/>)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    print_category_id = fields.Many2one(
        string='Print Category', comodel_name='product.print.category')
    print_count = fields.Boolean(
        string='To printing',
        help="Need to printing")

    @api.multi
    @api.depends('product_variant_ids.print_count')
    def _compute_to_print(self):
        for template in self:
            template.print_count = any(
                p.print_count for p in template.product_variant_ids)

    @api.model
    def create(self, vals):
        if vals.get('print_category_id', False):
            vals['print_count'] = True
        return super(ProductTemplate, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        template_ids = []
        for template in self:
            if template.print_category_id:
                if len(list(
                        set(vals.keys()) &
                        set(template.print_category_id.field_ids.
                            mapped('name')))):
                    template_ids.append(template.id)
        templates = self.browse(template_ids)
        super(ProductTemplate, templates).write({'print_count': True})
        products = self.env['product.product'].search(
            [('product_tmpl_id', 'in', tuple(template_ids))])
        products.write({'print_count': True})
        return res

    @api.multi
    def _print_report(self, datas, report_name, report_model):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': report_name,
            'datas': datas,
            'key2':  'client_print_multi',
            'context': self._context,
        }
