# coding: utf-8
# Copyright (C) 2016-Today: La Louve (<http://www.lalouve.net/>)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models


class ProductPrintCategory(models.Model):
    _name = 'product.print.category'
    _inherit = 'ir.needaction_mixin'

    # View Section
    @api.model
    def _needaction_count(self, domain=None, context=None):
        product_obj = self.env['product.product']
        return len(product_obj.search([('print_count', '=', True)]))

    # Fields Section
    name = fields.Char(string='Name', required=True)

    active = fields.Boolean(string='Active', default=True)

    company_id = fields.Many2one(
        string='Company', comodel_name='res.company', index=True,
        default=lambda self: self.env['res.company']._company_default_get())

    product_ids = fields.One2many(
        comodel_name='product.product', inverse_name='print_category_id')

    product_qty = fields.Integer(
        string='Products', compute='_compute_product_qty',
        store=True)

    product_to_print_ids = fields.One2many(
        comodel_name='product.product', compute='_compute_to_print',
        multi='print_count')

    product_to_print_qty = fields.Integer(
        compute='_compute_to_print', multi='print_count',
        string='Products To Print')

    field_ids = fields.Many2many(
        comodel_name='ir.model.fields',
        column1='category_id', column2='field_id',
        domain="[('model', '=', 'product.template')]")

    report_xml_id = fields.Many2one(
        comodel_name='ir.actions.report.xml', string='Report name',
        domain="[('model','in', ('product.product', 'product.template'))]"
    )

    # Compute Section
    @api.multi
    @api.depends(
        'product_ids.print_category_id',
        'product_ids.product_tmpl_id.print_category_id')
    def _compute_product_qty(self):
        for category in self:
            category.product_qty = len(category.product_ids)

    @api.multi
    def _compute_to_print(self):
        product_obj = self.env['product.product']
        for category in self:
            products = product_obj.search([
                ('print_category_id', '=', category.id),
                ('print_count', '=', True)])
            category.product_to_print_qty = len(products)
            category.product_to_print_ids = products
