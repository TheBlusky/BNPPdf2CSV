import glob
import subprocess
import re

def addToLineTxtToData():
	global lineData
	global lineTxt
	global state
	global allData
	# Concatenation du titre avec la ligne
	lineData['title']+=" "+re.sub(r'[ ]{2,}',' ',lineTxt.replace("\r","").replace("\n","")[lineData['startPos']:])
	
	# Si jamais la fin de la ligne est un montant
	if re.match(r'.*[ ]{5,}[0-9. ]{1,} , [0-9]{2}$',lineTxt.replace("\r","").replace("\n","")):
		lineData['amount']=float(re.search(r'.*[ ]{5,}([0-9. ]{1,} , [0-9]{2})$', lineTxt.replace("\r","").replace("\n","")).group(1).replace(".","").replace(" ","").replace(",","."))
		# On regarde l'emplacement savoir si c'est un revenu ou une dépense
		lineData['income']=re.search(r'^(.*,)[^,]*', lineTxt).group(1).__len__()>state['debPos']
		allData.append(lineData)
		return False
	return True
	
for filename in glob.glob("*.pdf"):
	print "[+] Analyse de "+filename
	# pdftotext permet d'avoir un PDF en Text, -layout permet de garder le format "tableau" en ASCII
	subprocess.call(["./pdftotext.exe", "-layout",filename,"tmp.txt"])
	# inline => est on dans le tableau ?, initial => Solde initial, final => Solde final, debPos => Position de la mention "debit"
	state={'inline':False,'initial':-1,'final':-1,'debPos':-1}
	# Variable contenant le resultat
	allData=[]
	lineData={'date':0,'amount':0,'income':False,'title':""}
	with open("tmp.txt") as file:
		for lineTxt in file.readlines():
			#Si deja dans une ligne, on le passe dans la routine
			if state['inline']:
				state['inline']=addToLineTxtToData()
			
			#Si Header colonne, on cherche la position du debit
			elif re.match(r'^[ ]*Date[ ]*Nature des op.rations[ ]*Valeur[ ]*D.bit[ ]*Cr.dit',lineTxt):
				state['debPos']=re.search(r'^(.*D.bit)', lineTxt).group(1).__len__()
				
			#Si ligne d'intro ou outro, on met a jour le solde
			elif re.match(r'^[ ]*SOLDE CREDITEUR AU',lineTxt):
				if state['initial']==-1:
					state['initial']=float(re.search(r'.*[ ]{5,}([0-9. ]{1,} , [0-9]{2})$', lineTxt.replace("\r","").replace("\n","")).group(1).replace(".","").replace(" ","").replace(",","."))
				else:
					state['final']=float(re.search(r'.*[ ]{5,}([0-9. ]{1,} , [0-9]{2})$', lineTxt.replace("\r","").replace("\n","")).group(1).replace(".","").replace(" ","").replace(",","."))
					
			#Si premiere ligne d'info, on le passe dans la routine
			elif re.match(r'^[ ]{1,10}[0-9]{2} \. [0-9]{2} ',lineTxt):
				state['inline']=True				
				lineData={'date':0,'amount':0,'income':False,'title':'','startPos':0}
				lineData['date']=re.search(r'^[ ]{1,10}([0-9]{2} \. [0-9]{2}) ', lineTxt).group(1).split(" . ")
				lineData['startPos']=re.search(r'^([ ]{1,10}[0-9]{2} \. [0-9]{2}[ ]*)', lineTxt).group(1).__len__()
				state['inline']=addToLineTxtToData()
	
	print "-> Ecriture de "+filename+".csv"	
	# On calcul le solde initital + toutes les transactions
	i=state['initial']
	with open(filename+".csv", "w") as file:
		for data in allData:
			file.write(data['date'][0]+"/"+data['date'][1]+";"+("" if data['income'] else "-")+"{:.2f}".format(data['amount'])+";"+data['title']+"\n")
			if data['income']:
				i+=data['amount']
			else:
				i-=data['amount']
			
	# On verifie que ca fait le solde final
	if state['final'] == i:
		print "-> Total concordant, fichier coherant"
	else:
		print "-> Erreur dans le calcul du fichier, verifiez le !"
