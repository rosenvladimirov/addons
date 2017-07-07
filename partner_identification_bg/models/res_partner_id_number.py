# -*- coding: utf-8 -*-
#
# © 2004-2010 Tiny SPRL http://tiny.be
# © 2010-2012 ChriCar Beteiligungs- und Beratungs- GmbH
#             http://www.camptocamp.at
# © 2015 Antiun Ingenieria, SL (Madrid, Spain)
#        http://www.antiun.com
#        Antonio Espinosa <antonioea@antiun.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models, fields, _
from openerp.exceptions import Warning as UserError
import logging
_logger = logging.getLogger(__name__)

class ResPartnerIdNumber(models.Model):
    _name = "res.partner.id_number"
    _order = "name"

    @api.constrains('name', 'category_id')
    def validate_id_number(self):
        return self.category_id.validate_id_number(self)

    name = fields.Char(
        string="ID Number", required=True,
        help="The ID itself. For example, Driver License number of this "
             "person")
    category_id = fields.Many2one(
        string="Category", required=True,
        comodel_name='res.partner.id_category',
        help="ID type defined in configuration. For example, Driver License")
    partner_id = fields.Many2one(string="Partner", required=True,
                                 comodel_name='res.partner',
                                 ondelete='cascade')
    partner_issued_id = fields.Many2one(
        string="Issued by", comodel_name='res.partner',
        help="Another partner, who issued this ID. For example, Traffic "
             "National Institution",
        domain="[('is_department','=',True),('parent_id.is_department','=',True)]")
    place_issuance = fields.Char(
        string="Place of Issuance",
        help="The place where the ID has been issued. For example the country "
             "for passports and visa")
    date_issued = fields.Date(
        string="Issued on",
        help="Issued date. For example, date when person approved his driving "
             "exam, 21/10/2009")
    valid_from = fields.Date(
        string="Valid from",
        help="Validation period stating date.")
    valid_until = fields.Date(
        string="Valid until",
        help="Expiration date. For example, date when person needs to renew "
             "his driver license, 21/10/2019")
    comment = fields.Text(string="Notes")
    status = fields.Selection(
        [('draft', 'New'),
         ('open', 'Running'),
         ('pending', 'To Renew'),
         ('close', 'Expired')])
    active = fields.Boolean(string="Active", default=True)

    @api.one
    def get_category(self):
        self.category_id.get_category()

    @api.one
    def set_category(self, model):
        self.category_id.set_category(model)

    @api.model
    def create(self, vals):
        _logger.info("Create %s" % vals)
        """ add vat check to create """
        if vals.get('name') and vals.get('category_id'):
            category = self.env['res.partner.id_category'].search([('id','=',vals.get('category_id'))])
            if category.fieldname != '':
                self.partner_id.write({category.fieldname: vals.get('name')})
        return super(ResPartnerIdNumber, self).create(vals)

    @api.multi
    def write(self, vals):
        """ add vat check to write """
        _logger.info("Write %s" % vals)
        for partner in self:
            if vals.get('category_id'):
                category = self.env['res.partner.id_category'].search([('id','=',vals.get('category_id'))])
                if category.fieldname != '':
                    self.partner_id.write({category.fieldname: partner.name})
        return super(ResPartnerIdNumber, self).write(vals)
