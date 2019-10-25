from collections import defaultdict

Kmin = defaultdict(dict)
Kdes = defaultdict(dict)
listedVels=[30,40,50,60,70,80,90,100,120]

Kmin[30][False]=2
Kmin[30][True]=4
Kdes[30][False]=2
Kdes[30][True]=4

Kmin[40][False]=5
Kmin[40][True]=7
Kdes[40][False]=5
Kdes[40][True]=7

Kmin[50][False]=9
Kmin[50][True]=11
Kdes[50][False]=10
Kdes[50][True]=12

Kmin[60][False]=14
Kmin[60][True]=15
Kdes[60][False]=18
Kdes[60][True]=17

Kmin[70][False]=20
Kmin[70][True]=19
Kdes[70][False]=29
Kdes[70][True]=24

Kmin[80][False]=29
Kmin[80][True]=24
Kdes[80][False]=48
Kdes[80][True]=32

Kmin[90][False]=41
Kmin[90][True]=29
Kdes[90][False]=74
Kdes[90][True]=42

Kmin[100][False]=58
Kmin[100][True]=36
Kdes[100][False]=107
Kdes[100][True]=52

Kmin[110][False]=79
Kmin[110][True]=43
Kdes[110][False]=164
Kdes[110][True]=66

Kmin[120][False]=102
Kmin[120][True]=50
Kdes[120][False]=233
Kdes[120][True]=80











