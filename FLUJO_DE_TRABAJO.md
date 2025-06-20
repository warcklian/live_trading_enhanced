🚀 FLUJO DE TRABAJO COLABORATIVO CON GIT
🏁 1. Clonar el repositorio (una sola vez)
Cada colaborador debe clonar el repositorio principal con HTTPS:


git clone https://github.com/organizacion/nombre-repo.git
cd nombre-repo
🌱 2. Crear una nueva rama por cada funcionalidad
Nunca trabajes directamente en main o master. Para empezar una nueva implementación o corrección, crea una rama hija:


git checkout main       # Asegúrate de partir desde main
git pull origin main    # Actualiza tu rama base
git checkout -b feature/nombre-funcionalidad
Ejemplos de nombres válidos:

feature/login-google

fix/error-validacion

hotfix/seguridad-api

🔨 3. Haz tus cambios localmente
Trabaja normalmente en tu editor (VSCode, etc.) y guarda tus avances.

✅ 4. Agregar, commitear y subir tus cambios
Desde el directorio raíz, ejecuta el script actualiza_colaborativo.bat para:

Agregar todos tus archivos.

Confirmar tu mensaje de commit.

Subir automáticamente la rama a GitHub.

O hazlo manualmente:


git add .
git commit -m "Describe brevemente los cambios"
git push origin feature/nombre-funcionalidad
🔁 5. Abrir un Pull Request (PR) para validar
Ve a GitHub y abre un Pull Request desde tu rama hacia main.

Título claro (ej: ✨ Nueva validación de usuarios)

Breve descripción de lo que resuelve o mejora

Asigna a quien revisará

🔍 6. Revisión de código
Otro miembro del equipo revisará tu código y dejará sugerencias si es necesario.

Si todo está bien, se aprueba el PR.

🔀 7. Merge a main SOLO vía PR aprobado
Una vez aprobado, se hace merge vía GitHub (no en local), para mantener control y trazabilidad.

🔄 8. Mantente actualizado
Siempre antes de empezar algo nuevo:


git checkout main
git pull origin main
Si tu rama se queda atrás de main, actualízala:


git checkout feature/mi-rama
git merge main
O si prefieres un historial más limpio:


git rebase main
🧭 REGLAS GENERALES DEL EQUIPO
✅ No trabajar directamente en main.

✅ Toda funcionalidad nueva debe ir en una rama separada.

✅ Commits deben tener mensajes claros y consistentes.

✅ Merge a main solo se hace vía Pull Request aprobado.

✅ Mantener sincronizada tu rama con main.

✅ Usar el script actualiza_colaborativo.bat para facilitar commits y evitar errores comunes.