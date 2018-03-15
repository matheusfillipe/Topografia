import math
def calculeI(progPrev,currentProg,cotaPrev,currentCota):
	return ((currentCota-cotaPrev)/(currentProg-progPrev))*100

def delta(azimutePrev,azimuteCurrent):
	res = abs(azimuteCurrent-azimutePrev)
	if(res>180):
		res = 360-res
	return res
def velocidade(i,classeProjeto,tipo):
	if i>=float(tipo[0]) and i<float(tipo[1]):
		if classeProjeto<=0:
			s = "120"
		elif classeProjeto <4:
			s = "100"
		elif classeProjeto <6:
			s = "80"
		else:
			s = "60"
		retorno = (s,"Plano")
	elif i>=float(tipo[2]) and i<float(tipo[3]):
		if classeProjeto<=0:
			s = "100"
		elif classeProjeto <3:
			s = "80"
		elif classeProjeto <4:
			s = "70"
		elif classeProjeto <6:
			s = "60"
		else:
			s = "40"
		retorno = (s,"Ondulado")
	else:
		if classeProjeto<=0:
			s = "80"
		elif classeProjeto <3:
			s = "60"
		elif classeProjeto <4:
			s = "50"
		elif classeProjeto <6:
			s = "40"
		else:
			s = "30"
		retorno = (s,"Montanhoso")
	return retorno
def fmax(velocidade):
	velocidades = {30:0.2,40:0.18,50:0.16,60:0.15,70:0.15,80:0.14,90:0.14,100:0.13,110:0.12,120:0.11}
	return velocidades[velocidade]

def rmin(velocidade,emax,fmax):
	return (velocidade**2)/(127*(emax+fmax))

def lsmin(velocidade,rutilizado=-1):
	if(rutilizado<0):
		return 0.556*velocidade
	return 0.036*((velocidade**3)/rutilizado)

def lsmax(rutilizado,delta):
	return (rutilizado*delta*math.pi)/180

def lsmedio(lsmin,lsmax):
	return (lsmin+lsmax)/2

def thetaS(lsutilizado,rutilizado):
	return lsutilizado/(2*rutilizado)

def xs(lsutilizado,theta):
	#=(lsutilizado*(1-(theta**2)/10+(theta**4)/216))
	return (lsutilizado*(1-(theta**2)/10+(theta**4)/216))
def ys(lsutilizado,theta):
	#=(lsutilizado*(theta/3-(theta**3)/42))
	return (lsutilizado*(theta/3-(theta**3)/42))
def fi(delta,theta):
	#=((PI()*H3)/180)-(2*T3)
	return ((math.pi*delta)/180)-(2*theta)
def d(rutilizado,fi):
	return rutilizado*fi

def d_curva_simples(rutilizado,delta):
	return (math.pi*rutilizado*delta)/180

def k(xs,rutilizado,theta):
	return xs-rutilizado*math.sin(theta)
def p(ys,rutilizado,theta):
	return ys-rutilizado*(1-math.cos(theta))
def tt(d,rutilizado,p,delta):
	return d+(rutilizado+p)*math.tan((delta/2)*math.pi/180)
def ets(epi,tt):
	return epi-tt
def esc(ets,lsutilizado):
	return ets+lsutilizado
def ecs(esc,d):
	return esc+d
def est(ecs,lsutilizado):
	return ecs+lsutilizado
def epi(eptAnt=-1,progAtual=-1,progAnt=-1,ttAnt=-1):
	if(eptAnt==-1):
		return progAtual
	return eptAnt+(progAtual-progAnt)-ttAnt

def t(rutilizado,delta):
	return rutilizado*math.tan((delta/2)*(math.pi/180))

def g20(rutilizado):
	return 1145.92/rutilizado

def epc(epiAtual,tAtual):
	return epiAtual-tAtual

def ept(epcAtual,dAtual):
	return epcAtual+dAtual

def deflexao_intermediaria(g20):
	return g20/2


