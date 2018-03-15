# Topografia
## Descrição

Plugin para qgis que possibilita o desenvolvimento do projeto geométrico de estradas. Permite a realização do traçado a partir de diretrizes sore o mapa com imagens de satélite e realiza cálculos de curvas horizontais, verticais e volumes.

## Estado de desenvolvimento

### Concluído

* GUI basica e funcionalidades básicas
* Geração da tabela Horizontal
* Cálculo de curvas horizontais
* Interface para traçado greide (perfil vertical)

### A Fazer

* Cálculo de curvas verticais
* Geração da tabela Vertical
* Geração dos perfis transverçais a partir de uma seção tipo
* Cálculo de Volumes
* Geração e Exportação dos desenhos

### Como Instalar

Coloque a estes arquivos dentro da pasta Topograph, no caminho .qgis/plugins/python/Topograph


## Bugs Conhecidos

* OpenLayers Plugin

```
QgsCsException: transformação à frente de (0.000000, 1.570796) PROJ.4:  +proj=utm +zone=23 +south +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs +para  +proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs Erro: tolerance condition error 
Traceback (most recent call last):

....

penlayers_plugin.py", line 227, in setMapCrs
    extMap = coordTrans.transform(extMap, QgsCoordinateTransform.ForwardTransform)
QgsCsException: transformação à frente de
(0.000000, 1.570796)
PROJ.4:  +proj=utm +zone=23 +south +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs +para  +proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs
Erro: tolerance condition error

```


## Links
[Qgis](https://www.qgis.org) - A Free and Open Source Geographic Information System 
