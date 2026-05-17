# Alertas — Ayuda

## ¿Qué hace esta sección?

Sistema de alertas basado en umbrales que te notifica automáticamente cuando el servidor está usando demasiados recursos o cuando alguna métrica supera un límite configurado.

---

## Cómo usar

### Reglas por defecto
MC Manager incluye 3 reglas predefinidas:
- CPU del servidor > 90% → Advertencia
- RAM del servidor > 95% → Crítico
- CPU del sistema > 90% → Advertencia

### Crear una regla personalizada
1. Escribe un nombre para la regla.
2. Selecciona la métrica a monitorear.
3. Elige la condición (mayor o menor que).
4. Ingresa el umbral numérico.
5. Selecciona la severidad.
6. Haz clic en **Agregar Regla**.

---

## Métricas disponibles

| Métrica | Descripción |
|---------|-------------|
| CPU Servidor (%) | Porcentaje de CPU del contenedor Minecraft |
| RAM Servidor (%) | Porcentaje de RAM del contenedor vs su límite |
| CPU Sistema (%) | Porcentaje de CPU del sistema completo |
| RAM Sistema (%) | Porcentaje de RAM del sistema operativo |

---

## Atajos de teclado

| Tecla / Acción | Descripción |
|----------------|-------------|
| Sidebar → Avanzado → Alertas | Navegar a esta sección |
| `?` | Abrir esta ayuda |

---

## Preguntas frecuentes

**¿Cómo se muestran las alertas?**
Como notificaciones "toast" en la esquina de la pantalla. También se registran en el historial de alertas de esta misma sección.

**¿Por qué la alerta no se dispara inmediatamente?**
Para evitar falsas alarmas por picos momentáneos, la alerta requiere 3 lecturas consecutivas por encima del umbral (6 segundos con el intervalo por defecto).

**¿Puedo recibir alertas por email o Telegram?**
No en esta versión. Las alertas son solo visuales dentro de MC Manager.

---

## Consejos

- En la laptop A8-3520M, un umbral de CPU al 85% es más conservador y apropiado.
- Configura una alerta de RAM > 90% para saber cuándo el servidor está al límite.
- El historial de alertas te ayuda a identificar cuándo y con qué frecuencia ocurren los picos de recursos.
