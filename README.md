# Proyecto Ingeniería de Datos: Mercado Electrico Español

El objetivo de este proyecto es recolectar los datos disponibilizados en el Sistema de Información del Operador del Sistema (Esios) pudiendo tener cuadros de mando, este proyecto se ha planteado como una ingesta en batch. Antes de explicar la arquitectura del proyecto, antes de empezar a explicar la Arquitectura del proyecto, vamos a explicar brevemente como funciona el Mercado Diario del Mercado Eléctrico Español.

## Mercado Eléctrico Diario

Nos estamos refiriendo desde luego al mercado mayorista eléctrico, que opera de forma diaria el operador de mercado eléctrico (OMIE, que sería como BME en el mercado financiero) y que suele conocerse como “pool” eléctrico.

Este término anglosajón de “pool” (que significa piscina en el idioma de Shakespeare) se deriva de la idea de que los vendedores y compradores mayoristas de energía eléctrica “arrojan” sus ofertas al mercado como si las lanzasen a una piscina.

Quienes arrojan las ofertas de venta son los generadores eléctricos (centrales nucleares, centrales de ciclo combinado, productores de energía con tecnología solar fotovoltaica, los propietarios de molinos que generan con energía eólica, etc..). Y quienes arrojan sus ofertas de compra son por lo general las compañías eléctricas, que luego actúan como comercializadores de los clientes finales (si bien algunos grandes consumidores industriales acuden directamente a comprar en el mercado).

Desde luego, como todo mercado, el objetivo final del “pool” es fijar un precio para cruzar la oferta y la demanda, cerrando así las transacciones de compraventa.

### ¿Qué significa marginalista?

Esencialmente significa que los productores han lanzado sus ofertas con diferentes precios, que podríamos ordenar de mayor a menor. Sin embargo, el precio que todos ellos recibirán por su energía será un mismo precio: el precio de mercado.

Que (y aquí viene el punto polémico) puede ser más alto que el precio al que estaban dispuestos a vender: aquél precio con el que habían ofertado.

Es decir, es el precio del margen, o precio marginal, el que se considera precio de mercado a cada hora del día.

De aquí derivan la mayor parte de críticas que se suelen realizar al mercado marginalista: el hecho de que algunos productores recibirán un precio por encima del precio al que podrían vender, y esto se puede entender injustificado o poco óptimo.

### Curva Agregada oferta y demanda

Con esta información se puede entender la "Curva Agregada Oferta y Demanda", donde se verán las diferentes ofertas de los generadores y demanda, llegando a un punto de interconexión que definará el Precio diario de la energía.

<div class="ai-center-all">
    <img width="800" src="https://elperiodicodelaenergia.com/wp-content/uploads/2018/11/Curva-agregada-de-demanda-y-oferta-1024x638.jpg?raw=true" alt="data stack">
</div>

## Arquitectura del Proyecto
Como se ha mencionado inicialmente, se ha planteado el proyecto como una Ingesta en Batch, para facilitar la instalación de los diferentes servicios se ha hecho mediante contenedores de Docker, evitando conflictos en la instalación, además de esta forma se automatiza la instalación de una forma más sencilla, antes de explicar los productos utilizados, se ha querido compartir un esquema del proyecto a partir del cual podemos hacernos una idea del proceso llevado a cabo.

<div class="ai-center-all">
    <img width="800" src="https://github.com/JorgeZapataBD/spain_electricity_market_ingest/blob/main/ArquitecturaProyectoEsios.png?raw=true" alt="data stack">
</div>

