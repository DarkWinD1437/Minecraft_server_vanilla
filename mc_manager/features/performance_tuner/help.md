# Rendimiento JVM — Ayuda

## ¿Qué hace esta sección?

Editor visual de los flags de la JVM (Java Virtual Machine) y la asignación de memoria del servidor. Modifica directamente `docker-compose.yml` sin necesidad de editar YAML manualmente.

---

## Cómo usar

### Presets
Los botones de preset aplican configuraciones optimizadas para diferentes casos de uso:
- **Balanceado (5GB)**: Configuración óptima para uso normal con el A8-3520M.
- **GC Agresivo (5GB)**: Minimiza las pausas por recolección de basura (para servers con muchos jugadores).
- **Mínimo (2GB)**: Para cuando necesitas liberar RAM para otras aplicaciones.
- **Grande (8GB)**: Si tienes más RAM disponible en el futuro.

### Configuración manual
1. Haz clic en **🔍 Leer docker-compose.yml** para cargar los valores actuales.
2. Modifica el campo "Memoria Heap" (ej: `5G`, `3G`, `512M`).
3. Modifica los flags GC si sabes lo que haces.
4. Haz clic en **💾 Guardar cambios**.
5. Reinicia el servidor para que los cambios surtan efecto.

---

## Flags JVM más importantes

| Flag | Descripción |
|------|-------------|
| `-XX:+UseG1GC` | Usar el recolector G1 (mejor para Minecraft) |
| `-XX:MaxGCPauseMillis=200` | Máximo 200ms de pausa por GC |
| `-XX:G1HeapRegionSize=8M` | Tamaño de regiones del heap |
| `-XX:+ParallelRefProcEnabled` | Procesamiento paralelo de referencias |

---

## Preguntas frecuentes

**¿Qué pasa si pongo más RAM de la que tiene el sistema?**
Java intentará reservarla y fallará al arrancar el servidor. Para la laptop con 8GB, no superes 5-6G (el SO necesita el resto).

**¿Cuándo debo cambiar los flags GC?**
Solo si tienes lag con los valores por defecto. Los presets ya están optimizados para el hardware.

**¿Necesito reiniciar después de cambiar?**
Sí, los flags JVM se leen al iniciar el servidor. Un cambio requiere parar y volver a iniciar el contenedor.

---

## Solución de problemas

- **El servidor no arranca tras el cambio**: La memoria configurada es mayor que la RAM disponible. Reduce el valor.
- **Error al guardar**: Verifica que `docker-compose.yml` tenga permisos de escritura.
- **Los flags no se aplican**: Comprueba que el servidor se haya reiniciado completamente (no solo pausado).
