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

    uic = fields.Char(
        string='Main UIC', compute='_compute_uic', store=False,
        inverse='_inverse_uic')

    #@api.model
    #def create(self, vals):
    #    """ add vat check to create """
    #    #_logger.info("Create %s" % vals)
    #    if vals.get('vat') and not vals.get('uic', False):
    #        if vals['vat'].upper().find('BG', 0, 2) != -1:
    #            vat = vals['vat']
    #            vals['uic'] = vat.\
    #                replace('BG', '').replace('.', '')
    #    return super(ResPartner, self).create(vals)

    #@api.multi
    #def write(self, vals):
    #    """ add vat check to write """
    #    _logger.info("Write %s" % vals)
    #    for partner in self:
    #        if vals.get('uic') and (vals.get('vat') and vals.get('vat').upper().find('BG', 0, 2) != -1):
    #            vat = vals['vat']
    #            vals['uic'] = vat.\
    #                replace('BG', '').replace('.', '')
    #    return super(ResPartner, self).write(vals)

    @api.multi
    @api.depends('id_numbers')
    def _compute_uic(self):
        for partner in self:
            uic_ids = partner.id_numbers.filtered(lambda r: (r.category_id.fieldname == 'uic' and r.category_id.is_company == partner.is_company))
            #_logger.info("Categori by uic: %s:%s" % (uic_ids.name, uic_ids.category_id))
            if uic_ids:
                partner.uic = uic_ids.name

    @api.multi
    def _inverse_uic(self):
        for partner in self:
            uic_ids = partner.id_numbers.filtered(lambda r: (r.category_id.fieldname == 'uic' and r.category_id.is_company == partner.is_company))
            #if (partner.vat and partner.vat.upper().find('BG', 0, 2) != -1 and len([x.id for x in uic_ids if x.uic != partner.vat.replace('BG', '')]) == 0):
            #    partner.uic = partner.vat.replace('BG', '')
            if not uic_ids and partner.uic:
                cat_id = self.env['res.partner.id_category'].default_create('uic')
                if cat_id and partner.uic:
                    self.env['res.partner.id_number'].create({'partner_id': partner.id, 'name': partner.uic, 'category_id': cat_id['id'], 'active': True, 'comment': 'UIC number registred by Taxadmin agency', 'status': 'open', })

    def _commercial_fields(self, cr, uid, context=None):
        return super(ResPartner, self)._commercial_fields(cr, uid, context=context) + ['uic']

    @api.model
    def search(self, domain, *args, **kwargs):
        global domain_old_uic
        if filter(lambda x: x[0] == 'uic', domain):
            #_logger.info("Start Filter %s:%s" % (domain, domain_old_supp))
            counter = len(filter(lambda x: x[0] == 'uic', domain))
            if counter > 1:
                j = 0
                for i,x in enumerate(domain):
                    if x[0] == 'uic' and j < counter-1:
                        #_logger.info("domain %s:%s:%s" % (x[0], i, j))
                        domain[i] = domain_old_uic[j]
                        j += 1
            else:
                domain_old_uic = []
            catg_ids = self.env['res_partner_id_category'].search(
                               [('"bg.uic"', 'iLike', validation_model)])
            part_code_operator = filter(lambda x: x[0] == 'uic', domain)[0][1]
            part_code_value = filter(lambda x: x[0] == 'uic', domain)[0][2]
            part_code_value = part_code_value.replace(' ', '').replace('.', '').upper()
            id_numbers = self.env['res_partner_id_number'].search(
                               [('name', part_code_operator, part_code_value), ('category_id','=',catg_ids)])
            domain = filter(lambda x: x[0] != '', domain)
            _logger.info("Filter %s" % domain)
            domain_old_uic.append(('id_numbers', 'in', [id_numbers]))
            domain += [domain_old_uic[-1]]
            _logger.info("After Filter %s:%s" % (domain, domain_old_uic))
        return super(ResPartner, self).search(domain, *args, **kwargs)
