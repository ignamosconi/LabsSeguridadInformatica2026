# Informe · Laboratorio 06 · Enumeración de servicios

**Grupo:** 05  
**Integrantes:** *Gastón Magni, Ignacio Mosconi, Matías Presuttari, Valentino Terreno*  
**Fecha:** 11/09/2026


## 0. Declaración de uso de IA

Se utilizó Claude (Anthropic) como asistente durante la resolución del laboratorio.
Usos concretos:
- Estructuración del informe y redacción de las secciones de análisis.
- Revisión de los comandos de enumeración y explicación de qué campo/header
  contiene cada hallazgo.
- Redacción del mini-research (sección en research.md).

El grupo ejecutó todos los comandos contra el entorno Docker de la cátedra,
verificó las salidas obtenidas y validó que el análisis sea consistente con
lo observado. Las flags se obtuvieron ejecutando las herramientas de enumeración,
no leyendo solucion.md ni el código del target.


## 1. Flags capturadas
```bash
Ignacio@DESKTOP-I81FL9D MINGW64 /.../LabsSeguridadInformatica2026 (lab06-grupo05)
$ bash ctf status 06

  ╭────────────────────────────────────────────────────────────╮  
  │                     PROGRESO · LAB 06                      │  
  ╰────────────────────────────────────────────────────────────╯  

   ✓  R1     Enumeracion de directorios  
   ✓  R2     Repositorio Git expuesto  
   ✓  R3     Metodos HTTP peligrosos habilitados  
   ✓  R4     Enumeracion de usuarios via API  
   ✓  R5     Fingerprinting de tecnologia  

  ██████████████████████████████  5/5 (100%)  

[ OK ] ¡Lab 06 COMPLETO! Ponete las pilas con la próxima unidad.  
```



