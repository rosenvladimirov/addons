# -*- coding: utf-8 -*-
#
# © 2004-2010 Tiny SPRL http://tiny.be
# © 2010-2012 ChriCar Beteiligungs- und Beratungs- GmbH
#             http://www.camptocamp.at
# © 2015 Antiun Ingenieria, SL (Madrid, Spain)
#        http://www.antiun.com
#        Antonio Espinosa <antonioea@antiun.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api, fields, _
from openerp.addons.base_vat.base_vat import _ref_vat
from openerp.exceptions import Warning as UserError

import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    id_numbers = fields.One2many(
        comodel_name='res.partner.id_number', inverse_name='partner_id',
        string="Identification Numbers")
    is_department = fields.Boolean(
        string='Is Department',
        help='Choice if a department',
        default=False)
    vat = fields.Char(
        string='Main VAT number', compute='_compute_vat', store=True,
        inverse='_inverse_vat')
    company_registry = fields.Char(string='Company Registry', size=64, compute='_compute_reg', store=True,
        inverse='_inverse_reg')
    numbers_pos = fields.Char(string='Partner Registers')

    def _auto_init(self, cr, context=None):
        """ normalise all vat fields in the database """
        cr.execute(
            "UPDATE res_partner "
            "SET vat = upper(replace(replace(vat, ' ', ''), '.', ''))")
        return super(ResPartner, self)._auto_init(cr, context=context)

    def __init__(self, pool, cr):
        """ remove check_vat constraint """
        super(ResPartner, self).__init__(pool, cr)
        for i, tup in enumerate(self._constraints):
            if hasattr(tup[0], '__name__') and tup[0].__name__ == 'check_vat':
                del self._constraints[i]

    @api.multi
    @api.depends('id_numbers')
    def _compute_vat(self):
        for partner in self:
            vat_ids = partner.id_numbers.filtered(lambda r: (r.category_id.fieldname == 'vat' and r.category_id.is_company == partner.is_company))
            _logger.debug("Categori by vat: %s:%s" % (vat_ids.name, vat_ids.category_id))
            if vat_ids:
                partner.vat = vat_ids.name

    @api.multi
    def _inverse_vat(self):
        for partner in self:
            vat_ids = partner.id_numbers.filtered(lambda r: (r.category_id.fieldname == 'vat' and r.category_id.is_company == partner.is_company))
            _logger.info("inverse vat %s:%s:%s" % (partner.id_numbers, vat_ids.name, partner.vat))
            if vat_ids and partner.vat and (vat_ids.name != partner.vat):
                vat_ids.write({'name': partner.vat})
            elif vat_ids and not partner.vat and (vat_ids.name != partner.vat):
                partner.vat = vat_ids.name
            elif not vat_ids:
                cat_id = self.env['res.partner.id_category'].default_create('vat')
                if partner.vat and cat_id:
                    self.env['res.partner.id_number'].create({'partner_id': partner.id, 'name': partner.vat, 'category_id': cat_id['id'], 'active': True, 'comment': 'VAT number validated by VIES', 'status': 'open', })

    @api.multi
    @api.depends('id_numbers')
    def _compute_reg(self):
        for partner in self:
            reg_ids = partner.id_numbers.filtered(lambda r: (r.category_id.fieldname == 'company_registry' and r.category_id.is_company == partner.is_company))
            _logger.debug("Categori by reg: %s:%s" % (reg_ids.name, reg_ids.category_id))
            if reg_ids:
                partner.company_registry = reg_ids.name

    @api.multi
    def _inverse_reg(self):
        for partner in self:
            reg_ids = partner.id_numbers.filtered(lambda r: (r.category_id.fieldname == 'company_registry' and r.category_id.is_company == partner.is_company))
            _logger.debug("inverse reg %s:%s:%s" % (partner.id_numbers, reg_ids.name, partner.company_registry))
            if reg_ids and partner.company_registry and (reg_ids.name != partner.company_registry):
                reg_ids.write({'name': partner.company_registry})
            elif reg_ids and not partner.company_registry and (reg_ids.name != partner.company_registry):
                partner.company_registry = reg_ids.name
            elif not reg_ids:
                cat_id = self.env['res.partner.id_category'].default_create('company_registry')
                if partner.company_registry and cat_id:
                    self.env['res.partner.id_number'].create({'partner_id': partner.id, 'name': partner.company_registry, 'category_id': cat_id['id'], 'active': True, 'comment': 'Trade Agency register number', 'status': 'open',})

    def _check_vat(self, vat):
        vat = vat.replace(' ', '').replace('.', '').upper()
        if not vat:
            return True
        _logger.debug("find VAT %s" % vat)
        vat_id = self.id_numbers.search([["name", "=", vat]], limit=1)
        if not vat_id:
            return True
        _logger.debug("Get objects category %s:%s:%s" % (vat, vat_id, vat_id.category_id.get_category()))
        online = False
        if not self._context.get('simple_vat_check'):
            online = self.env.user.company_id.vat_check_vies
        if online:
            #id_cat_obj = self.env['res.partner.id_category']
            #check_func = self.pool['res.partner'].vies_vat_check
            if vat_id.category_id.get_category() != 'eu.vat':
                vat_id.category_id.set_category('eu.vat')
        else:
            if vat_id.category_id.get_category() == 'eu.vat':
                vat_id.category_id.set_category()
        return vat_id.validate_id_number()
        #check_func = self.pool['res.partner'].simple_vat_check
        #vat_country, vat_number = self._split_vat(vat)
        #return check_func(self._cr, self._uid,
        #                  vat_country, vat_number, context=self._context)

    def _vat_check_errmsg(self, vat, partner_name):
        vat_no = "'CC##' (CC=Country Code, ##=VAT Number)"
        msg = _("VAT number validation for partner '%s' "
                "with VAT number '%s' failed.") % (partner_name, vat)
        msg += '\n'
        vat_country, vat_number = self._split_vat(vat)
        if vat_country.isalpha():
            vat_no = _ref_vat[vat_country] \
                if vat_country in _ref_vat else vat_no
            check_vies = self.env.user.company_id.vat_check_vies
            if check_vies:
                msg += _("The VAT number either failed the "
                         "VIES VAT validation check or did "
                         "not respect the expected format %s.") % vat_no
                return msg
        msg += _("This VAT number does not seem to be "
                 "valid.\nNote: the expected format is %s") % vat_no
        return msg

    @api.model
    def _parce_fileds(self, vals):
        if vals.get('id_numbers'):
            for id_number in vals['id_numbers']:
                _logger.debug("Parce fields ids %s" % id_number)
                fldname = self.env['res.partner.id_number'].search([('id', '=', id_number[1])]).category_id.fieldname
                if (fldname and fldname != '') and (id_number[2] and id_number[2].get('name')):
                    vals[fldname] = id_number[2]['name']
                    # Parce for fast search in pos
                    vals['numbers_pos'] = vals.get('numbers_pos','') + vals[fldname] + '|'
            if vals.get('numbers_pos'):
                vals['numbers_pos'] = vals['numbers_pos'][:-1]
        _logger.debug("Parce fields %s" % vals)
        return vals

    @api.model
    def create(self, vals):
        _logger.info("Create %s" % vals)
        """ add vat check to create """
        if vals.get('vat'):
            if not self._check_vat(vals['vat']):
                msg = self._vat_check_errmsg(
                    vals['vat'], vals.get('name', ''))
                raise UserError(msg)
            vals['vat'] = vals['vat'].\
                replace(' ', '').replace('.', '').upper()
            vals = self._parce_fileds(vals)
        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        """ add vat check to write """
        _logger.info("Write %s" % vals)
        for partner in self:
            if vals.get('vat'):
                if not partner.with_context(
                        {'simple_vat_check': True})._check_vat(vals['vat']):
                    partner_name = vals.get('name') or partner.name
                    msg = partner._vat_check_errmsg(vals['vat'], partner_name)
                    raise UserError(msg)
                vals['vat'] = vals['vat'].\
                    replace(' ', '').replace('.', '').upper()
            vals = partner._parce_fileds(vals)
        return super(ResPartner, self).write(vals)



    @api.multi
    def button_check_vat(self):
        self.ensure_one()
        if not self.check_vat():
            msg = self._vat_check_errmsg(
                self.vat, self.name or "")
            raise UserError(msg)
        else:
            raise UserError(_('VAT Number Check OK'))

#    @api.cr_uid_context
#    def _commercial_fields(self, cr, uid, context=None):
#        return super(ResPartner, self)._commercial_fields(cr, uid, context=context) + ['id_numbers']

    @api.model
    def search(self, domain, *args, **kwargs):
        global domain_old_vat
        if filter(lambda x: x[0] == 'vat', domain):
            #_logger.info("Start Filter %s:%s" % (domain, domain_old_supp))
            counter = len(filter(lambda x: x[0] == 'vat', domain))
            if counter > 1:
                j = 0
                for i,x in enumerate(domain):
                    if x[0] == 'vat' and j < counter-1:
                        #_logger.info("domain %s:%s:%s" % (x[0], i, j))
                        domain[i] = domain_old_vat[j]
                        j += 1
            else:
                domain_old_vat = []
            models = "vat"
            catg_obj = self.env['res.partner.id_category']
            catg_ids = catg_obj.search_read(
                               [('validation_model', 'ilike', 'vat')], ['name'])
            _logger.info("catd %s" % catg_ids)
            catg_ids = [o['id'] for o in catg_ids]
            part_code_operator = filter(lambda x: x[0] == 'vat', domain)[0][1]
            part_code_value = filter(lambda x: x[0] == 'vat', domain)[0][2]
            part_code_value = part_code_value.replace(' ', '').replace('.', '').upper()
            id_numbers = self.env['res.partner.id_number'].search_read(
                               [('name', part_code_operator, part_code_value), ('category_id','in',catg_ids)], ['name'])
            id_numbers = [o['id'] for o in id_numbers]
            domain = filter(lambda x: x[0] != '', domain)
            _logger.info("Filter %s" % domain)
            domain_old_vat.append(('id_numbers', 'in', id_numbers))
            domain += [domain_old_vat[-1]]
            _logger.info("After Filter %s:%s" % (domain, domain_old_vat))
        return super(ResPartner, self).search(domain, *args, **kwargs)
