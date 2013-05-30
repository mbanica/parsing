#!/usr/bin/python
import sqlite3,copy,unicodedata#ptr nume fis cu diacritice
from unidecode import unidecode # inloc diacr cu variantre ascii <-- de instalat
from sqlite3 import *
import mysql.connector #<-- de instalat 
from mysql.connector import errorcode
#MySQL charset = UTF-8 Unicode (utf8) MySQL connection collation=utf8_general_ci.
import mechanize,datetime, time,codecs,string
import nltk,sys,os,pprint  #<-- de instalat 
from nltk import word_tokenize, wordpunct_tokenize
import yaml
language=''
dirCrt=sys.path[0]
sys.path.append(dirCrt) # sa pot importa din dir crt orddict
import odict #<-- de instalat  ordered dict
#-------------------------
instr_add_candidat = ("INSERT INTO candidat "
               "(nume,prenume, adresa, telef, email,data_acces,data_mod_cv,data_ultim_applic,sex,an_nast,luna_nastere,zi_nastere,stare_civila,id,permis,data_permis,stagiu,scrisoare,interviu_online,obiectiv_text,salariu,beneficii,oras_domiciliu,oras_lucru,nivel_cariera,disponibil,experienta,studii,cursuri,cunost_pc,alte_cunost,max_realiz,max_esec,peste_5ani,vis,job_d,companie_d,depart_d,personalitate, data_inserare, site,stare) "
               "VALUES (%s, %s, %s,     %s,    %s,      %s,          %s,         %s,             %s,  %s,       %s ,           %s,           %s,          %s,         %s,       %s,       %s,        %s,              %s,          %s,       %s,           %s,            %s,           %s,         %s,          %s,      %s,       %s,       %s,        %s,          %s,        %s,      %s,       %s,    %s,    %s,    %s,    %s, %s, %s,%s,     %s        )")
#
instr_add_limba = ("INSERT INTO limbi "
               "(nume)"
               "values (%s)" )
instr_add_leglimba =(" INSERT into leg_candidat_limbi "
               " (nivel,idcandidat,idlimba) "
               "values ( %s, %s , %s)")
instr_add_departam=(" insert into depart_dorit "
                    "(idcandidat,depart)"
                    "values (%s,%s)")
instr_add_orase=(" insert into orase_lucru "
                 " (idcandidat,oras)"
                 "  values( %s,%s)")
#
instr_add_er=(" insert into er "
        "(date, site, file, name, details) "
        " values (%s,%s,%s,%s,%s) " )  
instr_add_log=(" insert into log "
        "(date, site, file, name,action,result, details) "
        " values (%s,%s,%s,%s,%s,%s,%s) " )
gsite='-'
lextins=[]
aMcandidat=[] # articol Mysql candidat
def citYAML(fis):  
    f=file(fis,'r')
    struct=yaml.load(f)
    f.close()
    return struct
def scrYAML(fis,listaStructuri):
    f=file(fis,'w')
    d=yaml.dump(listaStructuri,f)
    f.close()
def split(delimiters, string, maxsplit=0):
    import re
    regexPattern = '|'.join(map(re.escape, delimiters))
    return re.split(regexPattern, string, maxsplit)
def _15mini_interviu_vid():
    global lextins,aMcandidat
    lextins.append(['36 Cea mai mare realiz: ','-'])
    lextins.append(['37 Cel mai mare esec: ','-'])
    lextins.append(['38 Peste 5 ani? ','-'])
    lextins.append(['39 Vis, ideal: ','-'])
    lextins.append(['40 Job dorit : ','-'])
    lextins.append(['41 Compania dorita: ','-'])
    lextins.append(['42 Departamentul dorit: ','-'])
    lextins.append(['43 Personalitatea dvs: ','-'])
    return
def _14mini_interviu(m,language):
    global lextins,aMcandidat
    lSeparEtic=copy.deepcopy(param['EJOBS'][language]['mini interview section separators'])
    lSiruriTest=copy.deepcopy(param['EJOBS'][language]['mini interview section test strings'])
    dsort, elem1_extraPerechi=_13SPLIT_GENERAL_imperechiere_intreb_rasp(lSeparEtic,m)
    for intreb,[etic,rasp] in dsort.items(): # scrie camp extins, cu cele 2 expandari
        if not lSiruriTest['personalit'] in etic:
            rasp=rasp[:-2]# scos numerototarea din etic ptr a tratat si situatia lui george croitoru - are doar unele intrebari
        lextins.append([etic,rasp])     
def _13SPLIT_GENERAL_imperechiere_intreb_rasp(lSeparEtic,text):
    dsort=odict.OrderedDict (lSeparEtic)
    lDelimCompleta=dsort.keys()
    lDelimEfectiva=[]
    for d in lDelimCompleta:
        if d in text: #intreb apare in textul efectiv?
            lDelimEfectiva.append(d)
    # --- bifez rasp efective
    lRaspEfective=split(lDelimEfectiva, text, maxsplit=0)
    # izolez obiectiv- text ; raman lista perechi intreb:rasp
    elem1_extraPerechi=lRaspEfective[0].strip()# ob, cu care incepe, nu e o pereche intreb rasp; il elim ca sa mearga zip
    if elem1_extraPerechi=='':
        elem1_extraPerechi='-'
    #--- impercherea intreb/rasp
    del lRaspEfective[0:1] # ca sa pot face zip
    lIntrebRaspEfectiv=zip(lDelimEfectiva,lRaspEfective)
    # --- bifez rasp efective
    for intrebare,rasp in lIntrebRaspEfectiv:
        etic, val=dsort[intrebare]
        dsort[intrebare]= [etic, rasp.strip()] #celelalt eramin pe  '-'
    return dsort, elem1_extraPerechi
def _12aptitudini(a,fis,numepren,language):
    global lextins,aMcandidat
    lSeparEtic=copy.deepcopy(param['EJOBS'][language]['abilities section separators'])
    lSiruriTest=copy.deepcopy(param['EJOBS'][language]['abilities section test strings'])
    dsort, elem1_extraPerechi=_13SPLIT_GENERAL_imperechiere_intreb_rasp(lSeparEtic,a)
    # afisez toate rasp
    for intreb,[etic,rasp] in dsort.items(): # scrie camp extins, cu cele 2 expandari
        if lSiruriTest['Limbi'] in intreb:
            lLimbi=rasp.split(')')
            for slimba in lLimbi:
                if len(slimba)<2:
                    continue
                limba,nivel=slimba.split('(')
                limba=limba.strip(' ')
                nivel=nivel.strip(' ')
                lextins.append(['33.1 limba ',limba])
                lextins.append(['33.2 nivel ',nivel])  
            #  test camp limbi=corect
            nparst=rasp.count('(')
            npardr=rasp.count(')')
            if nparst==0 or (nparst!=npardr):
                _56w_erlog('er', Mcnx,Mcursor,[datetime.datetime.now().isoformat()[:16] ,gsite,fis,numepren,' ER 12 test limbi' ])
                #curs.execute("insert into log  values (NULL, ?,?,?,?,?,?,?) " ,(datetime.datetime.now().isoformat()[:16] ,'EJOBS',fis,numepren,'test limbi','er','' ))
                #conn.commit() 
                print ' er. 12  camp  limbi'
                return
            continue # sa nu scr a 2 oara limbile
        lextins.append([etic,rasp])     
    return
def _11educatie(e,language):
    global lextins,aMcandidat
    lSeparEtic=copy.deepcopy(param['EJOBS'][language]['education section separators'])
    dsort, elem1_extraPerechi=_13SPLIT_GENERAL_imperechiere_intreb_rasp(lSeparEtic,e)
    for intreb,[etic,rasp] in dsort.items(): # scrie camp extins, cu cele 2 expandari
        lextins.append([etic,rasp])     
    return  
def _10exp(e):
    global lextins,aMcandidat
    lextins.append(['30 experienta',e])
def _9extrag_separ_din_expgen(Html): # extrag boldurile- caz simplificat
    lHtml=string.split(Html,'<b>')
    del lHtml[0:1]
    lSepar=[]
    for b in lHtml:
        x=string.find(b,'</b>')
        lSepar.append(b[:x])
    #print '***',lSepar
    return lSepar
def _81exp_gen_vida():
    global lextins
    lextins.append(['29 exper generala ', '-'])
def _8exp_gen(eg,lSepar):
    global lextins
    lExper=split(lSepar, eg, maxsplit=0)
    del lExper[0:1]
    lExperDurata=zip(lSepar,lExper)
    for job,durata in lExperDurata:
        lextins.append(['29.1 exper generala -job ', job.strip()])
        lextins.append(['29.2 exper generala -durata ', durata.strip()])
def _7obiectiv(ob,language):
    global lextins,aMcandidat
    lSeparEtic=copy.deepcopy(param['EJOBS'][language]['objectif section separators'])
    lSiruriTest=copy.deepcopy(param['EJOBS'][language]['objectif section test strings'])
    dsort, ob_text=_13SPLIT_GENERAL_imperechiere_intreb_rasp(lSeparEtic,ob)
    lextins.append(['20 Obiectiv -text ', string.upper(ob_text)])
    # afisez toate rasp
    for intreb,[etic,rasp] in dsort.items(): # scrie camp extins, cu cele 2 expandari
        if lSiruriTest['Tip job'] in intreb:
            jobs=string.split(rasp,',')
            for job in jobs:
                lextins.append(['23 Tip job',job.strip()])
            continue
        if lSiruriTest['Departament'] in intreb:
            lDepart=string.split(rasp,',')
            for depart in lDepart:
                lextins.append(['24 Departament',depart.strip()])
            continue 
        lextins.append([etic,rasp])     
    return  
def _6interviu_online(int_ol):
    global lextins,aMcandidat
    lextins.append(['19 Interviu online',int_ol])
def _56w_erlog(tabela, Mcnx,Mcursor,lValCamp):
    global instr_add_er,instr_add_log
    if tabela=='er':
        Mcursor.execute(instr_add_er, lValCamp)
    else:
        Mcursor.execute(instr_add_log, lValCamp)
    Mcnx.commit()
def _55test_dublura(Mcnx,Mcursor):
    global aMcandidat
    try:
        an,lu,zi=aMcandidat[9],aMcandidat[10],aMcandidat[11]
        nume,prenume,id=aMcandidat[0],aMcandidat[1],aMcandidat[13]
        query = ("SELECT nume,prenume,data_ultim_applic,id FROM candidat WHERE an_nast = %s and luna_nastere= %s and zi_nastere =%s " )
                # "WHERE nume = '%s' ") - nu amers cu ghilm simple -trebuie far ghilim!  use parametrized arguments whenever possible, because it can automatically quote arguments for you when needed, and protect against sql injection.
        Mcursor.execute(query, (an,lu,zi)) #  ! nu (,limba!)
        if int(Mcursor.rowcount)== 0:# nici un posibil dublu(cu aceeasi data nast)
            return 'NU'
        else:
            gasit='NU'
            for (fnume,fprenume,fdata_ultim_applic, fid ) in Mcursor:   
                if fid==id:
                    gasit='DUBLURA_ID deci SKIP'
                    print 'DUBLURA_ID deci SKIP'
                    aMcandidat=[]
                    return gasit
                if fnume==nume and fprenume==prenume:
                    gasit='DUBLURA_NUME_NU_ID deci permit'
                    print 'DUBLURA_NUME_NU_ID deci permit'
                    aMcandidat=[]
                    #sterg cel vechi
                    return gasit
    except mysql.connector.Error as err:
        print ' EXCEPT _5.5 ',format(err)
        _56w_erlog('er', Mcnx,Mcursor,[datetime.datetime.now().isoformat()[:16] ,gsite,fis,numepren,' ER 55 '+ format(err) ])
        return 'NU'
def _54w(Mcnx,Mcursor,idtata,valcamp,instrInsert ):
    Mcursor.execute(instrInsert, (idtata,valcamp))
    Mcnx.commit()    
def _53wleg_candid_limb(Mcnx,Mcursor,niv,idcandidat,idlimba):
    global instr_add_leglimba
    Mcursor.execute(instr_add_leglimba, (niv,idcandidat,idlimba))
    Mcnx.commit()     
def _52wlimba(Mcnx,Mcursor,limba,param):
    global instr_add_limba,gsite,language
    try:
        if language=='english':
            dictEnglRom=copy.deepcopy(param['EJOBS'][language]['language translation'])
            if limba in dictEnglRom:
                limba=dictEnglRom[limba]
            else:
                pass #ramane romana
                _56w_erlog('er', Mcnx,Mcursor,[datetime.datetime.now().isoformat()[:16] ,gsite,fis,numepren,' ER 52A limba straina netradusa in romana' ])
                print ' EXCEPT _52.a   limba straina netradusa in romana'
        query = ("SELECT idlimbi,nume FROM limbi WHERE trim(nume) = %s  " )
                # "WHERE nume = '%s' ") - nu amers cu ghilm simple -trebuie far ghilim!  use parametrized arguments whenever possible, because it can automatically quote arguments for you when needed, and protect against sql injection.
        Mcursor.execute(query, (limba,)) #  ! nu (,limba!)
        if int(Mcursor.rowcount)== 0:
            Mcursor.execute(instr_add_limba, (limba,))
            Mcnx.commit()        
            return Mcursor.lastrowid
        else:
            idgasit=-1
            for (id, l   ) in Mcursor:        
                idgasit=id
            return idgasit
    except mysql.connector.Error as err:
        _56w_erlog('er', Mcnx,Mcursor,[datetime.datetime.now().isoformat()[:16] ,gsite,fis,numepren,' ER 52 '+ format(err) ])
        print ' EXCEPT _5.2 ',format(err)
        return -1
    return Mcnx.insert_id()    
def _51wcandidat(Mcnx,Mcursor,fis):
    global aMcandidat,instr_add_candidat,gsite
    try:
        if _55test_dublura(Mcnx,Mcursor)=='DUBLURA_ID deci SKIP':
            return 'DUBLURA_ID deci SKIP' # nu mai scrie
        #if _55test_dublura(Mcnx,Mcursor)=='DUBLURA_NUME_NU_ID deci UPD':
            #l-am sters pe cel vechi in _55 ..il tratez pe cel nou ca un normal    
            #return -1 # nu mai scrie
        if len( aMcandidat) != 42:
            print ' **_51a ',len(aMcandidat)
            _56w_erlog('er', Mcnx,Mcursor,[datetime.datetime.now().isoformat()[:16] ,gsite,fis,'-',' ER 51a '+len(aMcandidat)+' # 42 lungime canditat -er parsare!'])
            aMcandidat=[]
            return 'ER PARSE'
        Mcursor.execute(instr_add_candidat, aMcandidat)
        Mcnx.commit()
    except mysql.connector.Error as err:
        _56w_erlog('er', Mcnx,Mcursor,[datetime.datetime.now().isoformat()[:16] ,gsite,fis,'-',' ER 51b '+ format(err) ])
        print ' EXCEPT _5.1 ',format(err)
        aMcandidat=[]
        return 'ER W CANDIDAT'
        
    aMcandidat=[]
    return Mcursor.lastrowid
def _5printListaFinalaCV(lextins,numefis,Mcnx,Mcursor,param):
    global dirCrt,aMcandidat
    aMcandidat=[]
    ldepart=[]
    llimbi=[]
    lniv=[]
    lOraseLucru=[]
    fout=file(dirCrt+'/ok/'+numefis[:-5]+'_PARSAT.txt','w')
    n=0
    lextins.append(['44. data_inserare ',datetime.datetime.now().isoformat()[:16]  ])
    lextins.append(['45. site ','EJOBS' ])
    lextins.append(['46. stare candidat ','-' ])
    for etic, val in lextins:
        if etic[:2] not in ['23','24','29','33']:
            aMcandidat.append(val)
            n=n+1
            #print '===',n,etic,val
        #print etic,val
        if etic [:2] =='24':
            ldepart.append(val.strip().lower())
        if etic [:2] =='26':
            lor=val.split(',')
            for o in lor:
                lOraseLucru.append(o.strip().lower())
        if etic [:4] =='33.1':
            llimbi.append(val.strip().lower())  
        if etic [:4] =='33.2':
            lniv.append(val.strip().lower())            
        #print etic,' ---> ',val
        fout.write(etic+' ---> '+val+'\n')
    fout.close()
    idcandidat=_51wcandidat(Mcnx,Mcursor,numefis)
    if idcandidat in ['DUBLURA_ID deci SKIP','ER PARSE','ER W CANDIDAT' ]: #dublura sau eroare scriere; nu mai scriu fiii
        return idcandidat
    lLimbiNiv=zip(llimbi,lniv)
    for limba,niv in lLimbiNiv:
        idlimba=_52wlimba(Mcnx,Mcursor,limba,param)
        if idlimba!= -1: #n-au fost erori la scr acestei limbi
            _53wleg_candid_limb(Mcnx,Mcursor,niv,idcandidat,idlimba)
    for depart in ldepart:
        _54w(Mcnx,Mcursor,idcandidat,depart,instr_add_departam )
    for oras in lOraseLucru:
        _54w(Mcnx,Mcursor,idcandidat,oras,instr_add_orase)   
    aMcandidat=[]
    return 'INSERT'   
def adaug6_desfacut(s6):
    global lextins,aMcandidat
    data_ultimei_aplic=s6[:10]
    sex=s6[15]
    data_nast=s6[17:27]
    stare_civ=s6[28:]
    lextins.append(['8 Data ultimei aplicari',data_ultimei_aplic])
    lextins.append(['9 Sex',sex])
    #lextins.append(['8 Data nasterii ',data_nast]) 
    zi,lu,an=data_nast.split('.')
    lextins.append(['10.1 An nastere',an])
    lextins.append(['10.2 Luna nastere',lu])
    lextins.append(['11.3 Zi naster',zi])
    lextins.append(['12 Stare civila ', stare_civ])
def _5identificare(antet,language):
    global lextins,aMcandidat
    gunoi,antet=antet.split('021.209.3401')
    lSeparEtic=copy.deepcopy(param['EJOBS'][language]['identification section separators'])
    lSiruriTest=copy.deepcopy(param['EJOBS'][language]['identification section test strings'])
    dsort=odict.OrderedDict (lSeparEtic)
    lDelimCompleta=dsort.keys()
    lDelimEfectiva=[]
    for d in lDelimCompleta:
        if d in antet: #intreb apare in textul efectiv?
            lDelimEfectiva.append(d)
    lRaspEfective=split(lDelimEfectiva, antet, maxsplit=0)
    # izolez nume ; raman lista perechi intreb:rasp
    numepren=lRaspEfective[0].strip()# numele , cu care incepe, nu e o pereche intreb rasp; il elim ca sa mearga zip
    lnumepren=word_tokenize(numepren) 
    nume=lnumepren[-1]
    pren=string.join(lnumepren[:-1],' ')
    lextins.append(['1 Nume', string.upper(nume)])
    lextins.append(['2 Prenume', string.upper(pren)])
    del lRaspEfective[0:1] # ca sa pot face zip
    #
    lIntrebRaspEfectiv=zip(lDelimEfectiva,lRaspEfective)
    lastQuestionWithresponse=''
    for intrebare,rasp in lIntrebRaspEfectiv:
        lastQuestionWithresponse=intrebare
        etic, val=dsort[intrebare]
        dsort[intrebare]= [etic, rasp.strip()] #celelalt eramin pe  '-'
    # verific ca n-are in coada declartie proprie
    declaratie='-'
    [etic,rasp]=dsort[lastQuestionWithresponse]
    if lSiruriTest['ID'] in etic:
        if len(rasp)>7:
            declaratie=rasp[8:].strip() #iulia szente
            dsort[lastQuestionWithresponse]=[etic,rasp[:6]]
    if lSiruriTest['Permis'] in etic:
        xdataob=string.find(rasp,lSiruriTest['Data ob'])
        if xdataob!=-1:
            if len(rasp[xdataob:])>26:
                declaratie=rasp[xdataob+26:].strip()
                dsort[ lastQuestionWithresponse]=[etic,rasp[:xdataob+26].strip()]#refac  rasp, fara declaratia ce ede fapt next canp
        else:#nu a trecut si data obt
            if len(rasp)>5: # Cat.B
                declaratie=rasp[6:].strip()
                dsort[ lastQuestionWithresponse]=[etic,rasp[:6]]#refac  rasp, fara declaratia ce ede fapt next canp
    if lSiruriTest['Stagiu'] in etic:
        if len(rasp)>2  :
            declaratie=rasp[2:].strip()
            dsort[ lastQuestionWithresponse]=[etic,rasp[:2]]#refac  rasp, fara declaratia ce ede fapt next canp
    #---------- declaratie -----------------------
    for intreb,[etic,rasp] in dsort.items(): # scrie camp extins, cu cele 2 expandari
        if lSiruriTest['Data ultimei aplicari'] in intreb:
            adaug6_desfacut(rasp)
            continue
        xdataob=''
        if lSiruriTest['Permis conducere'] in intreb:
            if rasp!='-': # are permis--il despic
                xdataob=string.find(rasp,lSiruriTest['Data ob'])
                if xdataob==-1: # nu a completat data obt , desi are permis george teodor croitoru
                    #xvirg=string.find(rasp,',')
                    permis=rasp #[:xvirg]
                    data_obt_permis='-'
                else: #normal -arepermis, complet si data obt
                    permis=rasp[:xdataob]
                    data_obt_permis=rasp[-10:]
                [etic,rasp]=dsort[intreb]# in dreptul permisului sa nu fie si data obtinerii
                dsort[intreb]=[etic,permis]
                lextins.append(['14 Permis conducere',permis])
                lextins.append(['15 Data obtinerii',data_obt_permis])
            else:
                lextins.append(['14 Permis conducere','-'])
                lextins.append(['15 Data obtinerii','-'])
            continue
        lextins.append([etic,rasp])
    lextins.append(['18 Scrisoare intentie',declaratie])    
    return numepren
def _4clean(html):
    raw = nltk.clean_html(html)
    raw=raw.replace('\t','')
    raw=raw.replace('\n','')
    raw=unicodedata.normalize('NFKD',unicode(raw,'utf-8',errors='ignore')).encode('ascii','ignore')# elim non alphanumeric simona leafu
    raw=unidecode(unicode(raw,'utf-8',errors='ignore'))# unidec fara unico strica diacriticile ;unico da er ptr simboluri ciudate- anca morariu
    return raw
def _3ejobs(param,site,html,raw,fis,numefis,Mcnx,Mcursor):
    global lextins ,gsite , language
    print fis
    lSeparatoriSectiune=[]
    p=[]
    gsite=site
    if     'Last access:' in html     : 
        language='english'
        #_56w_erlog('er', Mcnx,Mcursor,[datetime.datetime.now().isoformat()[:16] ,'EJOBS',fis,'-',          ' er_3 -limba CV in engleza?'])
        print ' ---------------: engleza'
        #return
    elif   "Ultima accesare:" in html : language ='romanian'
    else :
        _56w_erlog('er', Mcnx,Mcursor,[datetime.datetime.now().isoformat()[:16] ,'EJOBS',fis,'-',          ' er_3 -limba CV #romana,engleza?'])
        return
    expGen=False
    sirExperGenerala= copy.deepcopy(param['EJOBS'][language]['general experience'])
    if sirExperGenerala in html:
        expGen=True
    lSeparatoriSectiune=copy.deepcopy(param['EJOBS'][language]['section separators'])
    #=p #else -setting of lSep.. is propagated in param????
    if expGen==False:
        del lSeparatoriSectiune[2:3] # impartirea se va face fara exp gerner 
    #lSeparatoriSectiune=['<p class=SectionTitle>INTERVIU ONLINE</p>','<p class=SectionTitle>obiectiv</p>','<p class=SectionTitle>experienta generala</p>','<p class=SectionTitle>experienta</p>','<p class=SectionTitle>educatie</p>','<p class=SectionTitle>aptitudini</p>','<p class=SectionTitle>mini interviu</p>']
    lBucHtml=split (lSeparatoriSectiune,html,maxsplit=0)
    lRaw=[]
    for buc in lBucHtml:
        try:
            lRaw.append(_4clean(buc))
        except:
            _56w_erlog('er', Mcnx,Mcursor,[datetime.datetime.now().isoformat()[:16] ,'EJOBS',fis,numepren,          ' er_3A - er unicode '+buc])
            return 
    try:
        try:
            numepren=_5identificare(lRaw[0],language)
        except:
            _56w_erlog('er', Mcnx,Mcursor,[datetime.datetime.now().isoformat()[:16] ,'EJOBS',fis,' -',          ' er_3B - er sectiune identificare'])
            return 
        _6interviu_online(lRaw[1])
        _7obiectiv(lRaw[2],language)
        if expGen==True:
            _8exp_gen(lRaw[3],_9extrag_separ_din_expgen(lBucHtml[3]))
            _10exp (lRaw[4])
            _11educatie(lRaw[5],language)
            _12aptitudini(lRaw[6],fis,numepren,language)
            if len(lRaw)==8:# exista miniinterviu
                _14mini_interviu(lRaw[7],language)
            else:
                _15mini_interviu_vid()
        else:
            _81exp_gen_vida()
            _10exp (lRaw[3])
            _11educatie(lRaw[4],language)
            _12aptitudini(lRaw[5],fis,numepren,language)
            if len(lRaw)==7:# exista miniinterviu
                _14mini_interviu(lRaw[6],language)
            else:
                _15mini_interviu_vid() 
        print '-'*30
        #pprint.pprint(lextins)
        stare=_5printListaFinalaCV(lextins,numefis,Mcnx,Mcursor,param)
        #curs.execute("insert into log  values (NULL, ?,?,?,?,?,?,?) " ,(datetime.datetime.now().isoformat()[:16] ,'EJOBS',fis,numepren,stare,'ok','' ))
        #conn.commit()

        _56w_erlog('log', Mcnx,Mcursor,[datetime.datetime.now().isoformat()[:16] ,'EJOBS',fis,numepren,stare,'ok',''])
    except:
        #curs.execute("insert into er   values (NULL, ?,?,?,?,?) "    ,(datetime.datetime.now().isoformat()[:16] ,'EJOBS',fis,numepren,          '' ))
        #conn.commit() 
        _56w_erlog('er', Mcnx,Mcursor,[datetime.datetime.now().isoformat()[:16] ,'EJOBS',fis,numepren,          ' er_3 -limba CV #romana?'])
    #------return
        
    #you declare a column of a table to be INTEGER PRIMARY KEY, then whenever you insert a NULL into that column of the table, the NULL is automatically converted into an integer which is one greater than the largest value of that column over all other rows in the table, or 1 if the table is empty.
def _2prelFis(param,fis,numefis,Mcnx,Mcursor):
    global lextins
    lextins=[]
    try:
        html=file(fis).read()
    except:
        print fis ,'----------nume cu diacritice'
        return 
    raw = nltk.clean_html(html)
    raw=raw.replace('\t','')
    raw=raw.replace('\n','')
    if 'ejobs' in raw:
        site='EJOBS'
    elif 'bestjobs' in raw:
        site='BESTJOBS'
    elif 'myjob' in raw:
        site='MYJOB'
    if site=='EJOBS':
        _3ejobs(param,site,html,raw,fis,numefis,Mcnx,Mcursor)
    else:
        print 'CV de la ', site, ' .....skip'
def _1fiecareAtasamentIntrare(param,Mcnx,Mcursor):
    dirIntrare=param['dir Input']
    lFis=os.listdir(unicode(dirIntrare,'utf-8'))#Changed in version 2.3: On Windows NT/2k/XP and Unix, if path is a Unicode object, the result will be a list of Unicode objects. Undecodable filenames will still be returned as string objects.
    for fis in lFis:
        _2prelFis(param,dirIntrare+'//'+fis,fis,Mcnx,Mcursor)  
if __name__ == '__main__':
    global param
    Mcnx = mysql.connector.connect(user='root', database='test',password='parola',host='localhost',buffered=True ) #buffered - ca sa nu dea er unread result found
    #ySQLdb.connect(host="localhost", user="root", passwd="nobodyknow", db="amit")
    Mcursor = Mcnx.cursor()
    #
    param=citYAML(dirCrt+'/'+'CV_html_2_BD.yaml') 
    _1fiecareAtasamentIntrare(param,Mcnx,Mcursor)
    pass
    #curs.close()
    #conn.close()
    #
    Mcursor.close()
    Mcnx.close()
    r=raw_input('prompt')