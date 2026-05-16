# Túnel Playit.gg — Ayuda

## ¿Qué hace esta sección?

Gestiona el servicio de túnel de red Playit.gg que permite a tus amigos conectarse al servidor Minecraft sin necesidad de abrir puertos en el router ni tener IP pública fija.

---

## ¿Cómo funciona Playit.gg?

Playit.gg es un proxy de red gratuito. Cuando el agente de Playit está corriendo:
1. Crea un túnel desde el servidor hasta los servidores de Playit.gg en internet.
2. Proporciona un link (ej: `abc123.auto.playit.gg:25565`) que apunta a tu servidor.
3. Tus amigos usan ese link en Minecraft > Multijugador > Añadir servidor.

---

## Cómo usar

1. Haz clic en **Iniciar Túnel** si no está activo.
2. Espera 20-30 segundos a que Playit establezca la conexión.
3. Haz clic en **Buscar Link** para escanear los logs y encontrar el link.
4. Comparte el link mostrado con tus amigos.
5. En Minecraft, ellos van a "Multijugador" → "Añadir servidor" → pegan el link.

**Primera vez:**
La primera vez que inicies el agente de Playit.gg, necesita autenticarse. Revisa los logs del contenedor `mc_tunel_red` para ver si hay un link de autenticación que debes abrir en el navegador.

---

## Atajos de teclado

| Tecla | Acción |
|-------|--------|
| `8` | Ir a Túnel |
| `?` | Abrir esta ayuda |

---

## Preguntas frecuentes

**¿Es gratuito Playit.gg?**
Sí, para uso básico es completamente gratuito. El plan gratis incluye túneles para juegos.

**¿Cambia el link cada vez que reinicio?**
En el plan gratuito, el subdominio puede cambiar. Con cuenta registrada, puedes tener subdominios permanentes.

**¿Necesito que el túnel y el servidor corran a la vez?**
Sí, ambos contenedores deben estar activos: `mc_servidor` y `mc_tunel_red`.

**¿El túnel afecta la latencia de los jugadores?**
Añade ~20-50ms de latencia adicional dependiendo de la ubicación de los servidores de Playit.

---

## Solución de problemas

- **Sin link en los logs**: La primera ejecución puede requerir autenticación. Revisa los logs de `mc_tunel_red` en el Log Viewer.
- **El túnel se desconecta**: Reinícialo con el botón "Reiniciar Túnel".
- **Los amigos no pueden conectarse**: Verifica que el servidor Minecraft también esté activo (no solo el túnel).
