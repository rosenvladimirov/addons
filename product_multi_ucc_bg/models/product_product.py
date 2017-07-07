# -*- coding: utf-8 -*-
# © 2012-2014 Guewen Baconnier (Camptocamp SA)
# © 2015 Roberto Lizana (Trey)
# © 2016 Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError


class ProductEan128(models.Model):
    _name = 'product.ucc'
    _description = "List of UCC/EAN128 code128 for a product."
    _order = 'sequence, id'

    name = fields.Char(string='UCC/EAN128/code128', size=13, required=True)
    sequence = fields.Integer(string='Sequence code128', default=0)
    product_id = fields.Many2one(
        string='Product', comodel_name='product.product', required=True)

    @api.multi
    @api.constrains('name')
    def _check_duplicates(self):
        for record in self:
            eans = self.search(
                [('id', '!=', record.id), ('name', '=', record.name)])
            if eans:
                raise UserError(
                    _('The UCC/EAN128 code128 Barcode "%s" already exists for product '
                      '"%s"') % (record.name, eans[0].product_id.name))


class ProductProduct(models.Model):
    _inherit = 'product.product'

    ucc_ids = fields.One2many(
        comodel_name='product.ucc', inverse_name='product_id',
        string='UCC/EAN128')
    ucc = fields.Char(
        string='Main UCC/EAN128', compute='_compute_ucc', store=True,
        inverse='_inverse_ucc')

    @api.multi
    @api.depends('ucc_ids')
    def _compute_ucc(self):
        for product in self:
            product.ucc = product.ucc_ids[:1].name

    @api.multi
    def _inverse_ucc(self):
        for product in self:
            if product.ucc_ids:
                product.ucc_ids[:1].write({'name': product.ucc})
            else:
                self.env['product.ucc'].create(self._prepare_ucc_vals())

    @api.multi
    def _prepare_ucc_vals(self):
        self.ensure_one()
        return {
            'product_id': self.id,
            'name': self.ucc,
        }

    @api.model
    def search(self, domain, *args, **kwargs):
        if filter(lambda x: x[0] == 'ucc', domain):
            ean_operator = filter(lambda x: x[0] == 'ucc', domain)[0][1]
            ean_value = filter(lambda x: x[0] == 'ucc', domain)[0][2]
            eans = self.env['product.ucc'].search(
                [('name', ean_operator, ean_value)])
            domain = filter(lambda x: x[0] != 'ucc', domain)
            domain += [('ucc_ids', 'in', eans.ids)]
        return super(ProductProduct, self).search(domain, *args, **kwargs)
