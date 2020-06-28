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


_logger = logging.getLogger(__name__)


class libro_venta_reportes_chile(models.TransientModel):
    _inherit = 'wizard.reportes.chile'

    @api.multi
    def _facturas_libro_venta(self):
        monto_exento=0
        search_domain = self._get_domain()
        search_domain += [
            ('state','in',['open','paid']),
            ('type','in',['out_invoice']),
            ('sii_code','in',['30','32','33','34','56'])
             ]
        docs = self.env['account.invoice'].search(search_domain, order='number asc')
        impuestos_obj = self.env['account.tax'].search([
            ('mostrar_v','=',True),
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
        exento=0
        neto=0
        for i in docs:
            if i.amount_tax==0:
                exento=i.amount_untaxed
                neto=0
            else:
                exento=0
                neto=i.amount_untaxed

            dict = OrderedDict()
            dict.update(dic)
            dict['Tipo']=i.document_class_id.name
            dict['Numero']=i.number
            dict['Fecha']=i.date_invoice
            dict['Rut']=i.partner_id.document_number
            dict['Cliente']=i.partner_id.name
            dict['Exento'] = exento
            dict['Neto']=neto
            dict['Total Impuestos']=i.amount_tax
            dict['Total']=i.amount_total
            for imp in i.tax_line_ids.filtered(lambda r: r.name in dic.keys()):
                dict[imp.name]+=imp.amount
            lista.append(dict)
        tabla = pd.DataFrame(lista)
        return tabla

    @api.multi
    def _nc_libro_venta(self):
        search_domain = self._get_domain()
        search_domain += [
            ('state','in',['open','paid']),
            ('type','in',['out_refund'])
             ]
        docs = self.env['account.invoice'].search(search_domain, order='number asc')
        impuestos_obj = self.env['account.tax'].search([
            ('mostrar_v','=',True),
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
        exento=0
        neto=0
        for i in docs:
            if i.amount_tax==0:
                exento=i.amount_untaxed
                neto=0
            else:
                exento=0
                neto=i.amount_untaxed
            dict = OrderedDict()
            dict.update(dic)
            dict['Tipo']=i.document_class_id.name
            dict['Numero']=i.number
            dict['Fecha']=i.date_invoice
            dict['Rut']=i.partner_id.document_number
            dict['Cliente']=i.partner_id.name
            dict['Exento']=-exento
            dict['Neto']=-neto
            dict['Total Impuestos']=-i.amount_tax
            dict['Total']=-i.amount_total
            for imp in i.tax_line_ids.filtered(lambda r: r.name in dic.keys()):
                dict[imp.name]+=-imp.amount
            lista.append(dict)
        tabla = pd.DataFrame(lista)
        return tabla

    @api.multi
    def _boletas_libro_venta(self):
        search_domain = self._get_domain()
        search_domain += [
            ('state','in',['open','paid']),
            ('type','in',['out_invoice']),
            ('sii_code','in',['35','38','39'])
             ]
        docs = self.env['account.invoice'].search(search_domain, order='number asc')
        impuestos_obj = self.env['account.tax'].search([
            ('mostrar_v','=',True),
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
        exento=0
        neto=0
        for i in docs:
            if i.amount_tax==0:
                exento=i.amount_untaxed
                neto=0
            else:
                exento=0
                neto=i.amount_untaxed

            dict = OrderedDict()
            dict.update(dic)
            dict['Tipo']=i.document_class_id.name
            dict['Numero']=i.number
            dict['Fecha']=i.date_invoice
            dict['Rut']=i.partner_id.document_number
            dict['Cliente']=i.partner_id.name
            dict['Exento']=exento
            dict['Neto']=neto
            dict['Total Impuestos']=i.amount_tax
            dict['Total']=i.amount_total
            for imp in i.tax_line_ids.filtered(lambda r: r.name in dic.keys()):
                dict[imp.name]+=imp.amount
            lista.append(dict)
        tabla = pd.DataFrame(lista)
        return tabla

    def _boletas_pos_libro_venta(self):
        search_domain = self._get_domain_boletas()
        search_domain += [
            ('sii_code','in',['35','38','39'])
             ]
        docs = self.env['pos.order'].search(search_domain, order='sii_document_number asc')
#        impuestos_obj = self.env['account.tax'].search([
#            ('mostrar_v','=',True),
#            ('company_id','=',self.company_id.id)])
        dic = OrderedDict([
            ('Tipo',''),
            ('Numero',''),
            ('Fecha',''),
            ('Rut',''),
            ('Cliente',''),
            ('Exento',0),
            ('Neto',0),
            ])
        # for record in impuestos_obj:
        #     dic.update({record.name:0})
        # dic.update({'Total Impuestos':0})
        # dic.update({'Total':0})
        lista = []
        exento=0
        neto=0
        for i in docs:
            exento=0
            neto=i.amount_total-i.amount_tax

            dict = OrderedDict()
            dict.update(dic)
            dict['Tipo']=i.document_class_id.name
            dict['Numero']=i.sii_document_number
            dict['Fecha']=i.date_order
            dict['Rut']=i.partner_id.document_number
            dict['Cliente']=i.partner_id.name
            dict['Exento']=exento
            dict['Neto']=neto
            dict['Total Impuestos']=i.amount_tax
            dict['Total']=i.amount_total
            lista.append(dict)
        tabla = pd.DataFrame(lista)
        return tabla


    @api.multi
    def _resumen_boletas_libro_venta(self):
        tabla = self._boletas_pos_libro_venta()
        if not tabla.empty:
            tabla = tabla.rename(
                columns={
                'Tipo':'Dia',
                'Numero':'Primera Boleta',
                'Rut':'Ultima Boleta',
                'Cliente':'Cantidad de Boletas'
                })
            tabla['Dia'] = tabla['Fecha']
            tabla = tabla.drop(['Fecha'], axis=1)
            aggregations = OrderedDict()
            for record in tabla.columns.values:
                aggregations.update([(record,'sum')])
            aggregations['Dia']='max'
            aggregations['Primera Boleta']='min'
            aggregations['Ultima Boleta']='max'
            aggregations['Cantidad de Boletas']='count'
            tabla = pd.DataFrame(tabla.groupby('Dia').agg(aggregations))
        return tabla

    @api.multi
    def _resumen_libro_venta(self):
        tabla1 = self._facturas_libro_venta()
        tabla2 = self._nc_libro_venta()
        tabla3 = self._boletas_libro_venta()
        union = pd.concat([tabla1,tabla2,tabla3])
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
    def _tabla_libro_venta(self,wizard=False):
        if wizard:
            wiz = self.search([('id','=',wizard)])
        else:
            wiz = self
        tabla1 = wiz._facturas_libro_venta()
        tabla2 = wiz._nc_libro_venta()
        tabla3 = wiz._boletas_libro_venta()
        union = pd.concat([tabla1,tabla2,tabla3])
        #if union.empty:
           # return 'error'
            #raise exceptions.Warning('No hay datos para mostrar')
        return union

