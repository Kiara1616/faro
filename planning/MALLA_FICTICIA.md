# Malla ficticia reproducible

`fixtures/malla_demo.json` es el único plan de la demo. Está marcado
`simulation_only: true` y no contiene IDs, productos ni cantidades operacionales
de ORICA.

Cada taladro tiene `id`, `product`, `planned_kg` (kilogramos),
`delivery_method`, `blocked` y `scenario`. El validador exige como mínimo:

- un taladro normal operable;
- un escenario cuyo texto indique una discrepancia de dictado/plan;
- un taladro bloqueado;
- IDs únicos, kg enteros positivos y método `brazo` o `manguera`.

La carga del archivo es determinista: dos lecturas de la misma versión generan
el mismo `DemoPlan`. Un archivo incompleto, duplicado o no ficticio falla antes
de crear el dominio o el simulador.

