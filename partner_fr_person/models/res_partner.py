# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    fr_person = fields.Char(compute='_compute_fr', store=False,
            string="FR Person", translate=True,
            help="Representer ot The Company. For example, Company manager.")
    fr_person_display = fields.Char(compute='_compute_fr_display', store=False,
            string="FR Person", translate=True,
            help="Representer ot The Company. For example, Company manager.")

    wh_person = fields.Char(compute='_compute_wh', store=False,
            string="FR Person", translate=True,
            help="Representer ot The Company. For example, Company manager.")
    id_function = fields.Many2one(
        comodel_name='res.partner.id_function',
        string="Function")

    @api.one
    @api.depends('child_ids', 'is_company')
    def _compute_fr(self):
        _logger.info("FR Person %s: company %s" % (self.child_ids, self.is_company))
        name = ''
        if self.is_company:
            for r in self.child_ids:
                _logger.info("FR Person e %s" % (r.id_function))
                for f in r.id_function:
                    if f.fieldname == 'fr_person':
                        name = name + r.name + ', '
                        _logger.info("FR Person ok %s:%s:%s" % (self, r.display_name, name))
            if name:
                self.fr_person = name[:-2]

    @api.one
    @api.depends('fr_person', 'child_ids', 'is_company')
    def _compute_fr_display(self):
        name = ''
        title = ''
        counts = 0
        if self.is_company:
            for r in self.child_ids:
                _logger.info("FR Person e %s" % (r.id_function))
                for f in r.id_function:
                    if f.fieldname == 'fr_person':
                        counts = counts + 1
                        name = name + r.name + ', '
                        if not title:
                            title = f.name
                        elif counts == 2:
                            title = title + _("'s")
                        _logger.info("FR Person ok disp: %s:%s:%s %s" % (self, r.display_name, title, name[:-2]))
            if name:
                self.fr_person_display = "%s %s" % (title, name[:-2])

    @api.one
    @api.depends('child_ids', 'is_company')
    def _compute_wh(self):
        _logger.info("WH Person %s: company %s" % (self.child_ids, self.is_company))
        if self.is_company:
            for r in self.child_ids:
                _logger.info("WH Person e %s" % (r.id_function))
                for f in r.id_function:
                    if f.fieldname == 'wh_person':
                        _logger.info("WH Person ok %s:%s" % (self, r.display_name))
                        self.wh_person = r.name
                        break

    @api.onchange('id_function','function')
    def on_change_id_function(self):
        if self.id_function:
            self.function = self.id_function.name

class ResPartnerIdFunction(models.Model):
    _name = "res.partner.id_function"
    _order = "name"

    def _get_fieldname(self):
        return [('fr_person', 'Representer of The company'), ('wh_person', 'Wharehause manager'),]

    name = fields.Char(
        string="Fucntion name", required=True, translate=True,
        help="Name of function on contact person. For example, 'Manager'")
    fieldname = fields.Selection(
        _get_fieldname,
        'Choice field name to fill', default='fr_person')
