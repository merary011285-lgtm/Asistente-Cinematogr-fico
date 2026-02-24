# 🎬 Asistente Cinematográfico PRO: IMAX V2.7

![Version](https://img.shields.io/badge/version-2.7-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Powered by](https://img.shields.io/badge/Powered%20By-Gemini%20%7C%20OpenAI%20%7C%20Flux-orange.svg)

**El Asistente Cinematográfico PRO** es una herramienta avanzada diseñada para directores, fotógrafos (DPs) y artistas digitales que buscan generar prompts de IA con precisión física y técnica de película de gran formato (IMAX 70mm).

## ✨ Características Principales (V2.7)

- **Firmas de Directores Maestros**: Estilos técnicos pre-configurados de Nolan, Villeneuve, Deakins, Lubezki, Spielberg, Ridley Scott y más.
- **Simulación IMAX 70mm**: Parámetros físicos de cámaras IMAX MSM 9802 y lentes anamórficos.
- **Multi-IA Image Gen**: Generación directa integrada con **Gemini/Imagen 3**, **Fal.ai (Flux)**, **OpenAI (DALL-E 3)** y **Replicate**.
- **Analizador de Guiones**: Convierte fragmentos de guion técnico en una lista de tomas cinematográficas automáticamente.
- **Diagramas de Iluminación**: Esquemas visuales automáticos (Mermaid) para la posición de luces (Key, Fill, Rim).

## 🛠️ Instalación y Uso Local

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/merary011285-lgtm/Asistente-Cinematogr-fico.git
   cd Asistente-Cinematogr-fico
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar Secretos**:
   Crea una carpeta `.streamlit` y dentro un archivo `secrets.toml` usando la plantilla:
   ```bash
   cp secrets_template.toml .streamlit/secrets.toml
   ```
   *Edita las API Keys en el archivo resultante.*

4. **Correr la App**:
   ```bash
   streamlit run cinematography_assistant.py
   ```

## 📋 Recomendaciones de Mejora (Roadmap)

1. **Gestión de Versiones**: Usar `git tag` para marcar hitos (v1.0, v2.0).
2. **Visuales del Repo**: Añadir una carpeta `/assets` con capturas de pantalla de la interfaz "Glassmorphism" para atraer usuarios.
3. **Licencia**: Considerar añadir un archivo `LICENSE` (Sugerencia: MIT) para facilitar la colaboración.
4. **Pruebas Automatizadas**: Implementar tests básicos de integración para las APIs de imagen.

---
**Desarrollado con ❤️ por Antigravity Hub.**
