# coding: utf-8
# Copyright (C) 2012-Today GRAP (http://www.grap.coop)
# @author Julien WESTE
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import _, api, fields, models
from openerp.exceptions import Warning as UserError

import logging
_logger = logging.getLogger(__name__)


class ProductPrintWizard(models.TransientModel):
    _name = 'product.print.wizard'

    line_ids = fields.One2many(
        comodel_name='product.print.wizard.line', inverse_name='wizard_id',
        string='Lines', default=lambda s: s._default_line_ids())
    report_xml_id = fields.Many2one(
        comodel_name='ir.actions.report.xml', string='Report name',
        domain="[('model','in', ('product.product', 'product.template'))]",
        default=lambda self, *a: self._context.get("default_report_xml_id", False)
    )

    @api.model
    def _default_line_ids(self):
        lines_vals = []
        context = self.env.context
        product_obj = self.env['product.product']

        if context.get('active_model', False) == 'product.print.category':
            domain = [
                ('print_category_id', '=', context.get('active_id', False)),
            ]
            if not context.get('all_products', False):
                domain.append(('print_count', '=', True))
            products = product_obj.search(domain)
        elif context.get('active_model', False) == 'product.product':
            product_ids = context.get('active_ids', [])
            products = product_obj.browse(product_ids)
        elif context.get('active_model', False) == 'product.template':
            template_ids = context.get('active_ids', [])
            products = product_obj.search([
                ('product_tmpl_id', 'in', template_ids),
            ])
        else:
            return False

        # Initialize lines
        products_without = products.filtered(lambda x: not x.print_category_id)
        if products_without:
                raise UserError(_(
                    "The following products has not print category defined."
                    " Please define one before.\n %s") % (
                        '\n'.join([x.name for x in products_without])
                    ))
        for product in products:
                lines_vals.append((0, 0, {
                    'product_id': product.id,
                    'print_category_id': product.print_category_id.id,
                    'quantity': 1,
                }))
        return lines_vals

    # View Section
    #@api.multi
    #def print_report(self):
    #    self.ensure_one()
    #    data = self._prepare_data()
    #    return self.env['report'].get_action(
    #        self, 'product_print_category.report_pricetag', data=data)

    @api.multi
    def _prepare_data(self):
        ids = []
        for x in self.line_ids:
            _logger.info("Records %s=>%s:%s" % (x, x.product_id.id, x.quantity))
            for p in range(0, x.quantity):
                ids.append(x.product_id.id)
        return ids

    @api.multi
    def _prepare_product_data(self):
        self.ensure_one()
        product_data = {}
        for line in self.line_ids:
            if line.product_id.id not in product_data:
                product_data[line.product_id.id] = line.quantity
            else:
                product_data[line.product_id.id] += line.quantity
        return product_data

    @api.multi
    def print_report(self):
        active_ids = self._prepare_data()
        _logger.info("Ids %s" % active_ids)
        active_id = active_ids[0]
        report_name = self.report_xml_id.report_name
        report_model = self.report_xml_id.model
        report_model_obj = self.env[self.report_xml_id.model].search([('id', 'in', active_ids)])
        #report_model_obj._ids = active_ids
        ctx = self._context.copy() or {}
        ctx.update({'active_id': active_id,
                    'active_ids': active_ids,
                    'active_model': report_model,
                    'render_func': 'render_product_label',
                    'report_name': report_name})
        #if report_model in ('product.product', 'product.template'):
        return report_model_obj.with_context(ctx)._print_report({'line_data': active_ids}, report_name, report_model)

        #return {
        #    'type': 'ir.actions.report.xml',
        #    'report_name': report_name,
        #    'datas': datas,
        #    'key2':  'client_print_multi',
        #    'context': {
        #        'active_model': self.model,
        #        'render_func': 'render_product_label',
        #        'report_name': report_name
        #    },
        #}

#class SaleCostSimulator(models.TransientModel):
#    _name = 'report.sale_cost_simulator.report_sale_simulation'
#
#    @api.multi
#    def get_xml_id(self, module, res_id):
#        ir_model_datas = self.env['ir.model.data'].search([
#            ('res_id', '=', res_id),
#            ('module', '=', module),
#            ('model', '=', 'res.company')])
#        return ir_model_datas and ir_model_datas[0].name or None
#
#    @api.multi
#    def render_html(self, data=None):
#        template = 'sale_cost_simulator.report_sale_simulation'
#        doc = self.env['report']._get_report_from_name(template)
#        selected_orders = self.env['simulation.cost'].browse(self.ids)
#        report = self.env['report'].browse(self.ids[0])
#        return report.render(template, {
#            'doc_ids': self.ids,
#            'doc_model': doc.model,
#            'docs': selected_orders,
#            'data': data and data or None,
#            'get_xml_id': partial(self.get_xml_id)})
