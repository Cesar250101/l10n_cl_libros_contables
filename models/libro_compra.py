from odoo import models, fields, api, exceptions
from datetime import date,datetime
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
import xlsxwriter
from io import StringIO
import base64
import pandas as pd
import numpy as np
import logging


class libro_compra_reportes_chile(models.TransientModel):
    _inherit = 'wizard.reportes.chile'

    @api.multi
    def _facturas_libro_compra(self):
        search_domain = self._get_domain_libro_compra()
        search_domain += [
            ('state','in',['open','paid']),
            ('type','in',['in_invoice']),
            ('sii_code','in',['30','32','33','34','45','46','55','56'])
            ]
        docs = self.env['account.invoice'].search(search_domain, order='reference asc')
        impuestos_obj = self.env['account.tax'].search([
            ('mostrar_c','=',True),
            ('company_id','=',self.company_id.id)])
        dic = OrderedDict([
            ('Tipo',''),
            ('Numero',''),
            ('Fecha',''),
            ('Rut',''),
            ('Cliente',''),
            ('Exento',0),
            ('Neto',0),
            ])
        for record in impuestos_obj:
            dic.update({record.name:0})
        dic.update({'Total Impuestos':0})
        dic.update({'Total':0})
        lista = []
        monto_exento=0
        for i in docs:
            exento=self.env[('account.invoice.tax')].search([('invoice_id','=',self.id),('name','=','Exento Venta')])
            for e in exento:
                monto_exento=e.base

            dict = OrderedDict()
            dict.update(dic)
            dict['Tipo']=i.document_class_id.name
            dict['Numero']=i.reference
            dict['Fecha']=i.date_invoice
            dict['Rut']=i.partner_id.document_number
            dict['Cliente']=i.partner_id.name
            dict['Exento']=monto_exento
            dict['Neto']=i.amount_untaxed
            dict['Total Impuestos']=i.amount_tax
            dict['Total']=i.amount_total
            for imp in i.tax_line_ids.filtered(lambda r: r.name in dic.keys()):
                dict[imp.name]+=imp.amount
            lista.append(dict)
        tabla = pd.DataFrame(lista)
        return tabla

    @api.multi
    def _nc_libro_compra(self):
        search_domain = self._get_domain()
        search_domain += [
            ('state','in',['open','paid']),
            ('type','in',['in_refund']),
            ('sii_code','in',['60','61'])
            ]
        docs = self.env['account.invoice'].search(search_domain, order='reference asc')
        impuestos_obj = self.env['account.tax'].search([
            ('mostrar_c','=',True),
            ('company_id','=',self.company_id.id)])
        dic = OrderedDict([
            ('Tipo',''),
            ('Numero',''),
            ('Fecha',''),
            ('Rut',''),
            ('Cliente',''),
            ('Exento',0),
            ('Neto',0),
            ])
        for record in impuestos_obj:
            dic.update({record.name:0})
        dic.update({'Total Impuestos':0})
        dic.update({'Total':0})
        lista = []
        monto_exento = 0
        for i in docs:
            exento=self.env[('account.invoice.tax')].search([('invoice_id','=',self.id),('name','=','Exento Venta')])
            for e in exento:
                monto_exento=e.base

            dict = OrderedDict()
            dict.update(dic)
            dict['Tipo']=i.document_class_id.name
            dict['Numero']=i.reference
            dict['Fecha']=i.date_invoice
            dict['Rut']=i.partner_id.document_number
            dict['Cliente']=i.partner_id.name
            dict['Exento']=monto_exento
            dict['Neto']=-i.amount_untaxed
            dict['Total Impuestos']=-i.amount_tax
            dict['Total']=-i.amount_total
            for imp in i.tax_line_ids.filtered(lambda r: r.name in dic.keys()):
                dict[imp.name]+=-imp.amount
            lista.append(dict)
        tabla = pd.DataFrame(lista)
        return tabla

    # @api.multi
    # def _din_libro_compra(self):
    #     search_domain = self._get_domain()
    #     search_domain += [
    #         ('state','in',['done'])
    #         ]
    #     docs = self.env['account.din'].search(search_domain, order='origin asc')
    #     impuestos_obj = self.env['account.tax'].search([
    #         ('mostrar_c','=',True),
    #         ('company_id','=',self.company_id.id)])
    #     dic = OrderedDict([
    #         ('Tipo',''),
    #         ('Numero',''),
    #         ('Fecha',''),
    #         ('Rut',''),
    #         ('Cliente',''),
    #         ('Exento',0),
    #         ('Neto',0)
    #         ])
    #     for record in impuestos_obj:
    #         dic.update({record.name:0})
    #     dic.update({'Total Impuestos':0})
    #     dic.update({'Total':0})
    #     lista = []
    #     for i in docs:
    #         dict = OrderedDict()
    #         dict.update(dic)
    #         dict['Tipo']=i.journal_id.name
    #         dict['Numero']=i.origin
    #         dict['Fecha']=i.date_din
    #         dict['Rut']=i.partner_id.rut
    #         dict['Cliente']=i.partner_id.name
    #         dict['Exento']=i.amount_exempt_usd*i.rate
    #         dict['Neto']=i.total_untaxed
    #         dict['Total Impuestos']=i.amount_tax
    #         dict['Total']=i.amount_total
    #         lista.append(dict)
    #     tabla = pd.DataFrame(lista)
    #     return tabla


    @api.multi
    def _resumen_libro_compra(self):
        tabla1 = self._facturas_libro_compra()
        tabla2 = self._nc_libro_compra()
        # tabla3 = self._din_libro_compra()
        # union = pd.concat([tabla1,tabla2,tabla3])
        union = pd.concat([tabla1, tabla2])
        if not union.empty:
	        union = union.drop(['Fecha','Rut','Cliente'], axis=1)
	        columnas = list(union)
	        aggregations = OrderedDict()
	        for record in columnas:
	            aggregations.update([(record,'sum')])
	        aggregations['Numero']='count'
	        aggregations['Tipo']='max'
	        #aggregations.pop('Tipo', None)
	        union = pd.DataFrame(union.groupby('Tipo').agg(aggregations))
        return union


    @api.multi
    def _tabla_libro_compra(self,wizard=False):
        if wizard:
            wiz = self.search([('id','=',wizard)])
        else:
            wiz = self
        tabla1 = wiz._facturas_libro_compra()
        tabla2 = wiz._nc_libro_compra()
        tabla3 = wiz._din_libro_compra()
        union = pd.concat([tabla1,tabla2,tabla3])
        return union
