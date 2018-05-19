import numpy as np
import math
class KNN:
    def __init__(self,k=3):
        self.x = np.array([])
        self.y = np.array([])
        self.k = k + 1 if k % 2 == 0 else k

    def fit(self,x,y):
        self.x = np.array(x)
        self.y = np.array(y)
        return self
    def dist(self,x1,x2):
        soma = 0.0
        for i,_ in enumerate(x1):
            soma += (x1[i]-x2[i])**2
        return math.sqrt(soma)

    def predict(self,X):
        k = self.k
        Y = np.array([])
        for i,x in enumerate(X):
            dist = []
            for j,y in enumerate(self.x):
                dist.append((self.dist(x,y),j))
            viz = sorted(dist)

            if k > len(viz):
                k = len(viz)
            rotulos = np.array([])
            for j in viz[:k]:
                rotulos = np.append(rotulos,self.y[j[1]])
            desvio = np.sqrt(np.var(rotulos))
            rotulo = np.mean(rotulos)
            while desvio > 0.10 and len(rotulos)>1:
                rotulos = np.delete(rotulos,-1,0)
                rotulo = np.mean(rotulos)
                desvio = np.sqrt(np.var(rotulos))
            Y = np.append(Y,rotulo)
        return Y

#print KNN(3).fit([[1,1],[1,0],[0,0]],[1,1,0]).predict([[0,1],[1,1]])



