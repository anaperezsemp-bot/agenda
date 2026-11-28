# Diseño

El diseño vive en Figma: [Agenda de conciertos · Diseño](https://www.figma.com/design/8DeoYhZEw3ALr1aepHb2kg).

- Página **Pantallas**: Agenda, Detalle y Filtros en móvil (390 px).
- Página **Componentes**: Botón, Día, Chip, Insignia, Etiqueta agotado, Fila concierto, Casilla, Opción, Campo y Dato.
- Variables y estilos de texto: colores, espaciados, radios y tipografía.

## Cómo se conectan Figma y el código

`web/tokens.css` es el único sitio con valores de diseño. `web/styles.css` solo usa sus variables.
Cada variable de Figma tiene su variable CSS con el mismo nombre (también aparece en el panel de Dev Mode):

| Figma | CSS |
| --- | --- |
| `color/accent` (colección Color) | `--color-accent` en `:root` |
| `color/accent` (colección Color oscuro) | `--color-accent` en `@media (prefers-color-scheme: dark)` |
| `space/16` | `--space-16` |
| `radius/lg` | `--radius-lg` |
| `size/control` | `--size-control` |
| `font/family` | `--font-family` |
| `font/size/base` | `--text-base` |
| `font/weight/bold` | `--weight-bold` |

El modo oscuro va en una colección aparte (Color oscuro) porque el plan gratuito de Figma solo permite un modo por colección.

## Iterar

1. Cambia lo que quieras en Figma: una variable para cambios globales o un componente o pantalla para cambios concretos.
2. Pasa el enlace al frame o di qué variables has cambiado.
3. Se actualiza `tokens.css` (si son variables) o `styles.css` y el HTML (si es estructura).
