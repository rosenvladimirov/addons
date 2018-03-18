# -*- coding: utf-8 -*-
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api, fields

class ProductMarginClassificationCheck(models.TransientModel):
    _name = 'product.margin.classification.check'

    template_ids = fields.One2many(string='Products', comodel_name='product.margin.classification.check.line', inverse_name='wizard_id', default=lambda s: s._default_line_ids())

    @api.model
    def _default_line_ids(self):
        lines_vals = []
        context = self.env.context
        product_obj = self.env['product.template']
        domain = []
        if context.get('active_model', False) == 'product.margin.classification':
            domain = [('margin_classification_id', '=', context.get('active_id', False))]
        else:
            domain = [('margin_classification_id', '!=', False), ('margin_state', 'in', ('cheap', 'expensive'))]
        products = product_obj.search(domain)
        for product in products:
                lines_vals.append((0, 0, {
                    'product_id': product.id
                }))
        return lines_vals

    @api.multi
    def _apply_theoretical_price(self, state_list):
        template_obj = self.env['product.template']
        for classification in self:
            templates = template_obj.search([
                ('margin_state', 'in', state_list)])
            templates.use_theoretical_price()

    @api.multi
    def apply_theoretical_price(self):
        self._apply_theoretical_price(['cheap', 'expensive'])

    @api.multi
    def apply_theoretical_price_cheap(self):
        self._apply_theoretical_price(['cheap'])

    @api.multi
    def apply_theoretical_price_expensive(self):
        self._apply_theoretical_price(['expensive'])


class ProductMarginClassificationCheckLine(models.TransientModel):
    _name = 'product.margin.classification.check.line'
    _rec_name = 'product_id'

    # Columns Section
    wizard_id = fields.Many2one(comodel_name='product.margin.classification.check')

    product_id = fields.Many2one(
        comodel_name='product.template', string='Product')

    default_code = fields.Char(
        comodel_name='product.margin.classification',
        string='Internal code',
        readonly=True, related='product_id.default_code')

    name = fields.Char(
        comodel_name='product.margin.classification',
        string='Product name',
        readonly=True, related='product_id.name')

    list_price = fields.Float(
        string='Sale Price',
        readonly=True, related='product_id.list_price')

    standard_price = fields.Float(
        string='Cost Price',
        readonly=True, related='product_id.standard_price')

    margin_classification_id = fields.Many2one(
        comodel_name='product.margin.classification',
        string='Margin Classification',
        readonly=True, related='product_id.margin_classification_id')

    theoretical_price = fields.Float(
        string='Theoretical Price',
        readonly=True, related='product_id.theoretical_price')

    theoretical_price_vat = fields.Float(
        string='Theoretical Price with VAT',
        readonly=True, related='product_id.theoretical_price_vat')

    theoretical_difference = fields.Float(
        string='Theoretical Difference',
        readonly=True, related='product_id.theoretical_difference')

    margin_state = fields.Selection(
        string='Theoretical Price State',
        readonly=True, related='product_id.margin_state')
