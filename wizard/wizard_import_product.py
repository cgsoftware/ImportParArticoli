# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import wizard
from osv import osv, fields
import tools
import base64
import pooler
from tempfile import TemporaryFile
import product
import math

view_form="""<?xml version="1.0"?>
<form string="Import Product Catalog">
    <image name="gtk-dialog-info" colspan="2"/>
    <group colspan="2" col="4">
        <separator string="Import Update Catalog" colspan="4"/>
       <field name="data" colspan="4"/>
        <label string="You have to import a .CSV file wich is encoded in UTF-8.\n
Please check that the first line of your file is one of the following:" colspan="4" align="0.0"/>
    </group>
</form>"""

fields_form={
    'data':{'string':'File', 'type':'binary', 'required':True},
}
def is_pair(x):
    return not x%2

def check_ean(ean13):
        #import pdb;pdb.set_trace()
        if not ean13:
            return False
        if len(ean13) <> 13:
            return False
        try:
            int(ean13)
        except:
            return False
        sum=0
        for i in range(12):
            if is_pair(i):
                sum += int(ean13[i])
            else:
                sum += 3 * int(ean13[i])
        check = int(math.ceil(sum / 10.0) * 10 - sum)
        if check != int(ean13[12]):
            return False
        return True

class wizard_import_product(wizard.interface):
    

    def _import_product_func(self, cr, uid, data, context):
        form=data['form']
        fileobj = TemporaryFile('w+')
        fileobj.write( base64.decodestring(form['data']) )
        # now we determine the file format
        #import pdb;pdb.set_trace()    
        fileobj.seek(0)
        pool = pooler.get_pool(cr.dbname)
        product_obj = pool.get('product.product')     
        partner_obj = pool.get('res_partner')
        par_imp_product_obj = pool.get('par.imp.product')
        idPar = data['id']
        lista_idspar = par_imp_product_obj.search(cr,uid,[('supplier_id', '=',idPar)])
        lista_parametri = par_imp_product_obj.read(cr, uid, lista_idspar, ['column_name_product','column_number_file_import','eval_function'], context) 
        for riga in  fileobj.readlines():
            riga = riga.replace('"', '')
            riga = riga.split(";")
            Articolo = dict() 
            for riga_par in lista_parametri:
                campo = riga_par['column_name_product']
                colonnacsv = int(riga_par['column_number_file_import'])-1
                if colonnacsv == -1:
                    #import pdb;pdb.set_trace()                    
                    # deve costruire il campo dalla funzione, i caratteri di costruzione
                    # sono separati dalla virgola, per o/ra somma soltanto le colonne interessate e /
                    # cli eventuali separatori inseriti 19/10/2010
                    funzione = riga_par['eval_function'].split(",")
                    calcolo =''
                    for car in funzione:
                        if type(eval(car)) == str:
                            calcolo=calcolo+car
                        else:
                            calcolo=calcolo+riga[int(car)-1]
                    Articolo[campo]= calcolo
                else:
                    Articolo[campo] = riga[colonnacsv] 
            # HA COSTRUITO IL DIZIONARIO CON L'ARTICOLO LO CERCA PER CODICE PER DECIDERE SE INSERIRE 
            # O MODIFICARE IL SOLO PREZZO PER ORA C&G 15/10/2010
            #import pdb;pdb.set_trace() 
            # CONTROLLO UNITA' DI MISURA
            if Articolo.has_key('uom_id'):            
                if Articolo['uom_id']:
                    argoment = [('name',"=",Articolo['uom_id'])]
                    item = pool.get('product.uom').search(cr,uid,argoment) 
                    if item:
                        Articolo['uom_id']=item[0]
                        Articolo['uom_po_id']=item[0]
                    else:
                        #import pdb;pdb.set_trace()
                        Articolo['uom_id']=1
                        # raise osv.except_osv(('Warning !'),('L unità di misura non può essere vuota !'))                        
                        Articolo['uom_po_id']=1                     
            # CONTROLLO Categoria Articolo
            if Articolo.has_key('categ_id'):
                if Articolo['categ_id']:
                    item = pool.get('product.category').search(cr,uid,[('name',"=",Articolo['categ_id'])]) 
                    if item:
                        Articolo['categ_id']=item[0]
                    else:
                        Articolo['categ_id']=1            
            # CONTROLLO Marchio Articolo
            if Articolo.has_key('marchio_ids'):                      
                if Articolo['marchio_ids']:
                    item = pool.get('marchio.marchio').search(cr,uid,[('name',"=",Articolo['marchio_ids'])]) 
                    if item:
                        Articolo['marchio_ids']=item[0]
                    else:
                        Articolo['marchio_ids']=0   
            #controlla i campi prezzo
            if Articolo.has_key('price'):
                Articolo['price'] = Articolo['price'].replace(',','.')     
            if Articolo.has_key('standard_price'):
                Articolo['standard_price'] = Articolo['standard_price'].replace(',','.')
                Articolo['list_price']=Articolo['standard_price']
            #import pdb;pdb.set_trace()
            if Articolo.has_key('ean13'): # CONTROLLA PRIMA CHE IL BAR CODE SIA VALIDO PER PROCEDERE
                if check_ean(Articolo['ean13']):
                    ok = True
                else:
                    ok = False
            else:
                ok = True
            if ok:
                RecArticolo = product_obj.search(cr,uid,[('default_code', '=',Articolo['default_code'])])
                if RecArticolo:
                    # ARTICOLO ESISTENTE
                    # import pdb;pdb.set_trace()
                    TemplateId=pool.get('product.product').read(cr, uid, RecArticolo, ['product_tmpl_id'])
                    ok = product_obj.write(cr,uid,RecArticolo,Articolo)
                    ok = pool.get('product.template').write(cr,uid,[TemplateId[0]['id']],Articolo)
                else:
                    #DEVE PREPARARE LA INSERT  con eventuali altri controlli aggiuntivi  
                    ArticoloId = product_obj.create(cr,uid,Articolo)
                    #import pdb;pdb.set_trace()
                    # INSERISCE I DATI FORNITORE
                    Fornitore = dict()
                    item = pool.get('product.product').search(cr,uid,[('id',"=",ArticoloId)])
                    TemplateId=pool.get('product.product').read(cr, uid, item, ['product_tmpl_id'])
                    for riga in TemplateId:
                        Template = riga['product_tmpl_id']
                        Fornitore = {
                                    'product_id':Template[0],
                                    'name':idPar,
                                    'qty':1,
                                    'min_qty':1,
                                    'delay':1,
                                    'product_uom': Articolo['uom_id']
                                    }
                        FornitoreArtId = pool.get('product.supplierinfo').create(cr,uid,Fornitore)
                    #import pdb;pdb.set_trace()            
        fileobj.close()
        return {}
    


    states={
        'init':{
            'actions': [],
            'result': {'type': 'form', 'arch': view_form, 'fields': fields_form,
                'state':[
                    ('end', 'Cancel', 'gtk-cancel'),
                    ('finish', 'Ok', 'gtk-ok', True)
                ]
            }
        },
        'finish':{
            'actions':[],
            'result':{'type':'action', 'action':_import_product_func, 'state':'end'}
        },
    }
    
    
wizard_import_product('res.partner.wizard.import.product')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

