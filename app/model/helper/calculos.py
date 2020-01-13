import math


def calculeI(progPrev, currentProg, cotaPrev, currentCota):
    return ((currentCota - cotaPrev) / (currentProg - progPrev)) * 100


def delta(azimutePrev, azimuteCurrent):
    res = abs(azimuteCurrent - azimutePrev)
    if (res > 180):
        res = 360 - res
    return res

def vmedia(x):
    terms = [
        1.7995760048853219e+002,
        -1.9589809033622782e+001,
        9.7608162682466526e-001,
        -2.4742990072266831e-002,
        3.5898025026505798e-004,
        -2.9860942431386416e-006,
        1.3228446165447730e-008,
        -2.4183434420566437e-011
    ]

    t = 1
    r = 0
    for c in terms:
        r += c * t
        t *= x
    return r


def velocidade(i, classeProjeto, tipo):
    if i >= float(tipo[0]) and i < float(tipo[1]):
        if classeProjeto <= 0:
            s = "120"
        elif classeProjeto < 4:
            s = "100"
        elif classeProjeto < 6:
            s = "80"
        else:
            s = "60"
        retorno = (s, "Plano")
    elif i >= float(tipo[2]) and i < float(tipo[3]):
        if classeProjeto <= 0:
            s = "100"
        elif classeProjeto < 3:
            s = "80"
        elif classeProjeto < 4:
            s = "70"
        elif classeProjeto < 6:
            s = "60"
        else:
            s = "40"
        retorno = (s, "Ondulado")
    else:
        if classeProjeto <= 0:
            s = "80"
        elif classeProjeto < 3:
            s = "60"
        elif classeProjeto < 4:
            s = "50"
        elif classeProjeto < 6:
            s = "40"
        else:
            s = "30"
        retorno = (s, "Montanhoso")
    return retorno


def fmax(velocidade):
  #  velocidades = {30: 0.2, 40: 0.18, 50: 0.16, 60: 0.15, 70: 0.15, 80: 0.14, 90: 0.14, 100: 0.13, 110: 0.12, 120: 0.11}
#    return velocidades[velocidade]
    return .19-velocidade/1600


def rmin(velocidade, emax, fmax):
    return (velocidade ** 2) / (127 * (emax + fmax))


def lsmin(velocidade, rutilizado=-1):
    if (rutilizado < 0):
        return 0.556 * velocidade
    return 0.036 * ((velocidade ** 3) / rutilizado)


def lsmax(rutilizado, delta):
    return (rutilizado * delta * math.pi) / 180


def lsmedio(lsmin, lsmax):
    return (lsmin + lsmax) / 2


def thetaS(lsutilizado, rutilizado):
    return lsutilizado / (2 * rutilizado)


def xs(lsutilizado, theta):
    # =(lsutilizado*(1-(theta**2)/10+(theta**4)/216))
    return (lsutilizado * (1 - (theta ** 2) / 10 + (theta ** 4) / 216))


def ys(lsutilizado, theta):
    # =(lsutilizado*(theta/3-(theta**3)/42))
    return (lsutilizado * (theta / 3 - (theta ** 3) / 42))


def fi(delta, theta):
    # =((PI()*H3)/180)-(2*T3)
    return ((math.pi * delta) / 180) - (2 * theta)


def d(rutilizado, fi):
    return rutilizado * fi

def d_curva_simples(rutilizado, delta):
    return (math.pi * rutilizado * delta) / 180

def r_curva_simples(d, delta):
    return 180 * d /(math.pi * delta)

def l_utilizado(rutilizado, v, delta_val):
    return (max(0.036*v**3/rutilizado, 0.556*v)+rutilizado*delta_val*math.pi/180)/2

def k(xs, rutilizado, theta):
    return xs - rutilizado * math.sin(theta)


def p(ys, rutilizado, theta):
    return ys - rutilizado * (1 - math.cos(theta))


def tt(d, rutilizado, p, delta):
    return d + (rutilizado + p) * math.tan((delta / 2) * math.pi / 180)


def ets(epi, tt):
    return epi - tt


def esc(ets, lsutilizado):
    return ets + lsutilizado


def ecs(esc, d):
    return esc + d


def est(ecs, lsutilizado):
    return ecs + lsutilizado


def epi(eptAnt=-1, progAtual=-1, progAnt=-1, ttAnt=-1):
    if (eptAnt == -1):
        return progAtual
    return eptAnt + (progAtual - progAnt) - ttAnt


def t(rutilizado, delta):
    return rutilizado * math.tan((delta / 2) * (math.pi / 180))


def g20(rutilizado):
    return 1145.92 / rutilizado


def epc(epiAtual, tAtual):
    return epiAtual - tAtual


def ept(epcAtual, dAtual):
    return epcAtual + dAtual


def deflexao_intermediaria(g20):
    return g20 / 2

def clotX(theta):
    return 1-theta**2/10+theta**4/216

def clotY(theta):
    return theta/3-theta**3/42
