# -*- coding: utf-8 -*-
#
# © 2004-2010 Tiny SPRL http://tiny.be
# © 2010-2012 ChriCar Beteiligungs- und Beratungs- GmbH
#             http://www.camptocamp.at
# © 2015 Antiun Ingenieria, SL (Madrid, Spain)
#        http://www.antiun.com
#        Antonio Espinosa <antonioea@antiun.com>
# ©  2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import api, models, fields
from openerp.exceptions import ValidationError, Warning as UserError
from openerp.tools.safe_eval import safe_eval
from openerp.tools.translate import _
from openerp.exceptions import Warning as UserError

import logging
_logger = logging.getLogger(__name__)

VALIDATION_MODELS = [
    ('al.nipt','NIPT (Numri i Identifikimit për Personin e Tatueshëm, Albanian VAT number).'),
    ('ar.cbu','CBU (Clave Bancaria Uniforme, Argentine bank account number).'),
    ('ar.cuit','CUIT (Código Único de Identificación Tributaria, Argentinian tax number).'),
    ('at.businessid','Austrian Company Register Numbers.'),
    ('at.uid','UID (Umsatzsteuer-Identifikationsnummer, Austrian VAT number).'),
    ('au.abn','ABN (Australian Business Number).'),
    ('au.acn','ACN (Australian Company Number).'),
    ('au.tfn','TFN (Australian Tax File Number).'),
    ('be.vat','BTW, TVA, NWSt, ondernemingsnummer (Belgian enterprise number).'),
    ('bg.egn','EGN (ЕГН, Единен граждански номер, Bulgarian personal identity codes).'),
    ('bg.pnf','PNF (ЛНЧ, Личен номер на чужденец, Bulgarian number of a foreigner).'),
    ('bg.vat','VAT (Идентификационен номер по ДДС, Bulgarian VAT number).'),
    ('bg.uic','UIC (Единен идентификационен код, Bulgarian UIC number).'),
    ('br.cnpj','CNPJ (Cadastro Nacional da Pessoa Jurídica, Brazillian company identifier).'),
    ('br.cpf','CPF (Cadastro de Pessoas Físicas, Brazillian national identifier).'),
    ('ch.ssn','Swiss social security number (“Sozialversicherungsnummer”).'),
    ('ch.uid','UID (Unternehmens-Identifikationsnummer, Swiss business identifier).'),
    ('ch.vat','VAT, MWST, TVA, IVA, TPV (Mehrwertsteuernummer, the Swiss VAT number).'),
    ('cl.rut','RUT (Rol Único Tributario, Chilean national tax number).'),
    ('cn.ric','RIC No.'),
    ('co.nit','NIT (Número De Identificación Tributaria, Colombian identity code).'),
    ('cusip','CUSIP number (financial security identification number).'),
    ('cy.vat','Αριθμός Εγγραφής Φ.Π.Α. (Cypriot VAT number).'),
    ('cz.dic','DIČ (Daňové identifikační číslo, Czech VAT number).'),
    ('cz.rc','RČ (Rodné číslo, the Czech birth number).'),
    ('de.vat','Ust ID Nr.'),
    ('de.wkn','Wertpapierkennnummer (German securities identification code).'),
    ('dk.cpr','CPR (personnummer, the Danish citizen number).'),
    ('dk.cvr','CVR (Momsregistreringsnummer, Danish VAT number).'),
    ('do.cedula','Cedula (Dominican Republic national identification number).'),
    ('do.rnc','RNC (Registro Nacional del Contribuyente, Dominican Republic tax number).'),
    ('ean','EAN (International Article Number).'),
    ('ec.ci','CI (Cédula de identidad, Ecuadorian personal identity code).'),
    ('ec.ruc','RUC (Registro Único de Contribuyentes, Ecuadorian company tax number).'),
    ('ee.ik','Isikukood (Estonian Personcal ID number).'),
    ('ee.kmkr','KMKR (Käibemaksukohuslase, Estonian VAT number).'),
    ('es.ccc','CCC (Código Cuenta Corriente, Spanish Bank Account Code)'),
    ('es.cif','CIF (Certificado de Identificación Fiscal, Spanish company tax number).'),
    ('es.cups','CUPS (Código Unificado de Punto de Suministro, Supply Point Unified Code)'),
    ('es.dni','DNI (Documento nacional de identidad, Spanish personal identity codes).'),
    ('es.iban','Spanish IBAN (International Bank Account Number).'),
    ('es.nie','NIE (Número de Identificación de Extranjeros, Spanish foreigner number).'),
    ('es.nif','NIF (Número de Identificación Fiscal, Spanish VAT number).'),
    ('es.referenciacatastral','Referencia Catastral (Spanish real estate property id)'),
    ('eu.at_02','SEPA Identifier of the Creditor (AT-02)'),
    ('eu.eic','EIC (European Energy Identification Code).'),
    ('eu.nace','NACE (classification for businesses in the European Union).'),
    ('eu.vat','VAT (European Union VAT number).'),
    ('fi.alv','ALV nro (Arvonlisäveronumero, Finnish VAT number).'),
    ('fi.associationid','Finnish Association Identifier.'),
    ('fi.hetu','HETU (Henkilötunnus, Finnish personal identity code).'),
    ('fi.ytunnus','Y-tunnus (Finnish business identifier).'),
    ('fr.nif','NIF (Numéro d’Immatriculation Fiscale, French tax identification number).'),
    ('fr.nir','NIR (French personal identification number).'),
    ('fr.siren','SIREN (a French company identification number).'),
    ('fr.siret','SIRET (a French company establishment identification number).'),
    ('fr.tva','n° TVA (taxe sur la valeur ajoutée, French VAT number).'),
    ('gb.nhs','NHS (United Kingdom National Health Service patient identifier).'),
    ('gb.sedol','SEDOL number (Stock Exchange Daily Official List number).'),
    ('gb.vat','VAT (United Kingdom (and Isle of Man) VAT registration number).'),
    ("gr.vat","FPA, ΦΠΑ, ΑΦΜ (Αριθμός Φορολογικού Μητρώου, the Greek VAT number)."),
    ('grid','GRid (Global Release Identifier).'),
    ('hr.oib','OIB (Osobni identifikacijski broj, Croatian identification number).'),
    ('hu.anum','ANUM (Közösségi adószám, Hungarian VAT number).'),
    ('iban','IBAN (International Bank Account Number).'),
    ('ie.pps','PPS No (Personal Public Service Number, Irish personal number).'),
    ('ie.vat','VAT (Irish tax reference number).'),
    ('imei','IMEI (International Mobile Equipment Identity).'),
    ('imo','IMO number (International Maritime Organization number).'),
    ('imsi','IMSI (International Mobile Subscriber Identity).'),
    ('is_.kennitala','Kennitala (Icelandic personal and organisation identity code).'),
    ('is_.vsk','VSK number (Virðisaukaskattsnúmer, Icelandic VAT number).'),
    ('isan','ISAN (International Standard Audiovisual Number).'),
    ('isbn','ISBN (International Standard Book Number).'),
    ('isil','ISIL (International Standard Identifier for Libraries).'),
    ('isin','ISIN (International Securities Identification Number).'),
    ('ismn','ISMN (International Standard Music Number).'),
    ('iso6346','ISO 6346 (International standard for container identification)'),
    ('iso9362','ISO 9362 (Business identifier codes).'),
    ('issn','ISSN (International Standard Serial Number).'),
    ('it.codicefiscale','Codice Fiscale (Italian tax code for individuals).'),
    ('it.iva','Partita IVA (Italian VAT number).'),
    ('lei','LEI (Legal Entity Identifier).'),
    ('lt.pvm','PVM (Pridėtinės vertės mokestis mokėtojo kodas, Lithuanian VAT number).'),
    ('lu.tva','TVA (taxe sur la valeur ajoutée, Luxembourgian VAT number).'),
    ('lv.pvn','PVN (Pievienotās vērtības nodokļa, Latvian VAT number).'),
    ('mc.tva','n° TVA (taxe sur la valeur ajoutée, Monacan VAT number).'),
    ('meid','MEID (Mobile Equipment Identifier).'),
    ('mt.vat','VAT (Maltese VAT number).'),
    ('mx.rfc','RFC (Registro Federal de Contribuyentes, Mexican tax number).'),
    ('my.nric','NRIC No.'),
    ('nl.brin','Brin number (Dutch number for schools).'),
    ('nl.bsn','BSN (Burgerservicenummer, Dutch national identification number).'),
    ('nl.btw','BTW-nummer (Omzetbelastingnummer, the Dutch VAT number).'),
    ('nl.onderwijsnummer','Onderwijsnummer (Dutch student school number).'),
    ('nl.postcode','Postcode (Dutch postal code).'),
    ('no.mva','MVA (Merverdiavgift, Norwegian VAT number).'),
    ('no.orgnr','Orgnr (Organisasjonsnummer, Norwegian organisation number).'),
    ('pl.nip','NIP (Numer Identyfikacji Podatkowej, Polish VAT number).'),
    ('pl.pesel','PESEL (Polish national identification number).'),
    ('pl.regon','REGON (Rejestr Gospodarki Narodowej, Polish register of economic units).'),
    ('pt.nif','NIF (Número de identificação fiscal, Portuguese VAT number).'),
    ('ro.cf','CF (Cod de înregistrare în scopuri de TVA, Romanian VAT number).'),
    ('ro.cnp','CNP (Cod Numeric Personal, Romanian Numerical Personal Code).'),
    ('rs.pib','PIB (Poreski Identifikacioni Broj, Serbian tax identification number).'),
    ('ru.inn','ИНН (Идентификационный номер налогоплательщика, Russian tax identifier).'),
    ('se.orgnr','Orgnr (Organisationsnummer, Swedish company number).'),
    ('se.vat','VAT (Moms, Mervärdesskatt, Swedish VAT number).'),
    ('si.ddv','ID za DDV (Davčna številka, Slovenian VAT number).'),
    ('sk.dph','IČ DPH (IČ pre daň z pridanej hodnoty, Slovak VAT number).'),
    ('sk.rc','RČ (Rodné číslo, the Slovak birth number).'),
    ('sm.coe','COE (Codice operatore economico, San Marino national tax number).'),
    ('tr.tckimlik','T.C.'),
    ('us.atin','ATIN (U.S.'),
    ('us.ein','EIN (U.S.'),
    ('us.itin','ITIN (U.S.'),
    ('us.ptin','PTIN (U.S.'),
    ('us.rtn','RTN (Routing transport number).'),
    ('us.ssn','SSN (U.S.'),
    ('us.tin','TIN (U.S.'),
    ("other", "Your defineted python code"),
    ]

class ResPartnerIdCategory(models.Model):
    _name = "res.partner.id_category"
    _order = "name"

    def _default_validation_code(self):
        return _("\n# Python code. Use failed = True to specify that the id "
                 "number is not valid.\n"
                 "# You can use the following variables :\n"
                 "#  - self: browse_record of the current ID Category "
                 "browse_record\n"
                 "#  - id_number: browse_record of ID number to validate")

    def _default_fld(self):
        return {
                'vat': {'code': 'vat_vies', 'name': 'VAT number', 'active': True, 'validation_model': 'eu.vat', 'validation_model_base': 'eu.vat', 'fieldname': 'vat'},
                'company_registry': {'code': 'trade_register', 'name': 'Trade Agency register number', 'active': True, 'validation_model': 'other', 'validation_model_base': 'other', 'fieldname': 'company_registry'},
                }

    def _get_fieldname(self):
        return [('vat', 'Inditification code for VAT registrations'), ('company_registry', 'Trade Agency register number'),]

    code = fields.Char(
        string="Code", size=16, required=True,
        help="Abbreviation or acronym of this ID type. For example, "
             "'driver_license'")
    name = fields.Char(
        string="ID name", required=True, translate=True,
        help="Name of this ID type. For example, 'Driver License'")
    active = fields.Boolean(string="Active", default=True)
    validation_model = fields.Selection(VALIDATION_MODELS, 'Integrated validation Models',
                                     required=True, default='eu.vat')
    validation_model_base = fields.Char(
        string="Integrated validation old Models", required=True,
        help="Name of this ID type. For example, 'Driver License'")
    validation_code = fields.Text(
        'Python validation code',
        help="Python code called to validate an id number.",
        default=_default_validation_code)
    commercial_field = fields.Boolean(string="Is added to commercial fields", default=False)
    fieldname = fields.Selection(
        _get_fieldname,
        'Choice field name to fill', default='vat')
    is_company = fields.Boolean(string="Only for company", default=True)

    @api.model
    def default_create(self, fieldname):
        record = self.search([('fieldname', '=', fieldname)], limit=1)
        cat_default = self._default_fld().get(fieldname)
        #_logger.debug("Default Category 1: %s:%s" % (record, cat_default))
        if not record and cat_default:
            record = self.create(cat_default)
        _logger.debug("Default Category 1: %s" % record)
        return record

    @api.one
    def get_category(self):
        #for cat in self:
        #_logger.info("Category 1: %s" % self)
        return self.validation_model

    @api.multi
    def set_category(self, model):
        for cat in self:
            if model:
                old = cat.validation_model
                cat.write({"validation_model": model, "validation_model_base": old})
            else:
                cat.write({"validation_model": cat.validation_model_base})

    @api.onchange('validation_model')
    def _change_validation_model(self):
        if self.validation_model != 'other':
            exec_validation_code = "eval.validate('id_number.name')\n"
            self.validation_code = exec_validation_code
            self.code = [ x for x in VALIDATION_MODELS if x[0] == self.validation_model ][0][1]

    @api.multi
    def _validation_eval_context(self, id_number):
        self.ensure_one()
        return {'self': self,
                'id_number': id_number,
                }

    @api.multi
    def validate_id_number(self, id_number):
        """Validate the given ID number
        The method raises an openerp.exceptions.ValidationError if the eval of
        python validation code fails
        """
        self.ensure_one()
        eval_context = self._validation_eval_context(id_number)
        ret = True
        try:
            if self.validation_model != 'other':
                exec "from stdnum.%s import %s" % (self.validation_model.split(".")[0], self.validation_model.split(".")[1])
                eval_context.update({"eval": eval(self.validation_model.split(".")[1])})
                #_logger.info("Eval %s:%s" % (id_number.name, eval_context))
                eval_context['eval'].validate(id_number.name)
            else:
                safe_eval(self.validation_code,
                          eval_context,
                          mode='exec',
                          nocopy=True)
        except Exception as e:
            ret = False
            raise UserError(
                _('Error when evaluating the id_category validation code:'
                  ':\n %s \n(%s)') % (self.name, e))
        if eval_context.get('failed', False):
            ret = False
            raise ValidationError(
                _("%s is not a valid %s identifier") % (
                    id_number.name, self.name))
        return ret
