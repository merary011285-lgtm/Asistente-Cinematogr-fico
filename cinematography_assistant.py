import streamlit as st
import json
import os
from openai import OpenAI
import google.generativeai as st_genai 
from google import genai 
import librosa
import numpy as np
import tempfile

# Set page config for a premium look
st.set_page_config(
    page_title="Cinematographic Assistant AI",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a premium, dark-mode, glassmorphism aesthetic
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: #f0f2f6;
    }
    .stButton>button {
        background: linear-gradient(45deg, #ff4b2b, #ff416c);
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 8px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 15px rgba(255, 75, 43, 0.4);
    }
    .json-output {
        background-color: #1e222d;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b2b;
        font-family: 'Courier New', Courier, monospace;
    }
    h1, h2, h3 {
        color: #ffffff !important;
    }
    .sidebar .sidebar-content {
        background-color: #161b22;
    }
</style>
""", unsafe_allow_html=True)

# Prompt templates embedded directly to remove external JSON dependency
TEMPLATES = {
  "director_styles": {
    "Épico / Escala Masiva (Nolan)": "Grand scale architectures, visceral realism, physical practical effects, vast landscapes, 1.43:1 full IMAX height.",
    "Atmosférico / Ciencia Ficción (Villeneuve)": "Atmospheric fog, silhouette lighting, brutalist architecture, monochromatic or bi-color palettes, 1.90:1 digital IMAX.",
    "Roger Deakins (Naturalista)": "Motivated naturalistic lighting, muslin bounce, mid-wide 35mm focal lengths, extreme contrast precision, sharp clean textures.",
    "Emmanuel Lubezki (Inmersivo)": "Natural light only (magic hour), ultra-wide 12-24mm, immersive long takes, zero grain, visceral proximity to subject.",
    "Robert Richardson (Gótico/Halo)": "Strong rim lighting, HALO top-down effect, blooming highlights, high color contrast, Panavision anamorphic texture.",
    "Greig Fraser (Táctil/LED)": "Chiaroscuro (shadow play), digital-native textures, LED-screen ambient light, shallow depth of field, epic scope.",
    "Steven Spielberg (Bypass/Haze)": "Janusz Kaminski style, bleach bypass ENR process, desaturated color, heavy grain, overlit blooming highlights, hazy diffuse lighting.",
    "Ridley Scott (Épico Desaturado)": "Dariusz Wolski style, huge epic scale, painterly desaturated tones, natural available light emphasis, realistic documentary-style immersion.",
    "Estilo Documental Rudo": "Handheld 65mm feel, natural lighting, sweat and dirt detail, muted colors, high texture."
  },
  "lens_presets": {
    "Panavision Ultra 70 (Anamórfico)": "2x squeeze, intense oval bokeh, horizontal blue lens flares, sharp center with edge falloff.",
    "IMAX Hasselblad (Esférico)": "Tack sharp from corner to corner, zero distortion, deep depth of field, 15/70mm resolution.",
    "Cooke Anamórfico Vintage": "Warm tones, subtle lens flares, painterly bokeh, organic texture.",
    "Arri Alexa 65 (Digital Gran Formato)": "Ultra clean, massive dynamic range, modern glass characteristics."
  },
  "film_stocks": [
    "Kodak Vision3 500T (Poca luz, tonos fríos)",
    "Kodak Vision3 250D (Luz día, natural)",
    "Kodak Eastman Double-X (Blanco y Negro)",
    "Fuji Eterna (Alta saturación, verdes/azules profundos)"
  ],
  "shot_angles": {
    "Plano Gran General (EWS)": "Establishing the vast environment, character is small in frame, 1.43:1 ratio.",
    "Plano General (WS)": "Full body visible, clear relationship with environment.",
    "Plano Medio (MS)": "Waist up, focusing on interaction and wardrobe detail.",
    "Primer Plano (CU)": "Tight on face, shallow depth of field, intense 70mm skin texture.",
    "Ángulo Contrapicado (Heroico)": "Looking up at character, making them appear powerful.",
    "Cenital / Vista de Pájaro": "Looking down, showing isolation or objective perspective.",
    "Ángulo Holandés (Tensión)": "Tilted horizon, creating tension and unease."
  },
  "color_palettes": {
    "Clásico Teal & Orange": "Cool shadows, warm skin tones, high dynamic range pop.",
    "Desaturado / Bleach Bypass": "High contrast, gritty, muted colors, metallic feel.",
    "Tecnicolor Heredado": "Deep reds and blues, high saturation, nostalgic 1950s epic feel.",
    "Monocromo (Double-X)": "Hyper-detailed black and white, deep blacks, glowing silver highlights.",
    "Neón Noir": "Vibrant pinks and cyans against deep darkness."
  }
}

def generate_prompt(scene, character, wardrobe, color, director, lens, stock, angle_name, angle_desc, engine):
    # Mapping técnico
    is_anamorphic = "Anamórfico" in lens or "Anamorphic" in lens
    aspect_ratio = "2.76:1 (Ultra Panavision)" if is_anamorphic else "1.43:1 (IMAX Full)"
    
    technical_details = f"Shot on IMAX MSM 9802 15/70mm film, {lens} lenses, {stock} film stock. Aspect ratio {aspect_ratio}."
    
    # Anclas de Consistencia (en inglés para la IA)
    consistency_block = f"Character trait: {character}. Wardrobe: {wardrobe}. Color Palette: {color}."
    
    # Optimización del Motor
    engine_suffix = ""
    if engine == "Midjourney":
        ratio = "2.76:1" if is_anamorphic else "1.43:1"
        engine_suffix = f" --ar {ratio} --v 6 --stylize 250"
    elif engine == "DALL-E 3":
        engine_suffix = " Wide-screen cinematic mode, highly detailed."

    # Prompt final (Totalmente en Inglés)
    full_prompt = (
        f"{angle_name}: {scene}. {angle_desc}. {consistency_block}. {director}. {technical_details}. "
        f"Key visual traits: {'oval bokeh, horizontal lens flares, ' if is_anamorphic else ''}"
        f"extreme detail, naturalistic grain, high dynamic range, 12k resolution texture, visceral atmosphere.{engine_suffix}"
    )
    
    # Lógica de Iluminación para Mermaid
    diagram = f"graph TD\n    CAM[Cámara IMAX] --- SUB[({character})]\n"
    if "Natural" in director or "Deakins" in director or "Naturalista" in director:
        diagram += "    SUN[Fuente de Luz Natural] --> SUB\n    BOUNCE[Rebotador Muslin] --> SUB"
    elif "Richardson" in director:
        diagram += "    HALO[Luz Halo Cenital] --> SUB\n    BACK[Contraluz de Recorte] --> SUB"
    elif "Spielberg" in director:
        diagram += "    BLOOM[Luz Sobreexpuesta (Haze)] --> SUB\n    BACK[Contraluz Fuerte] --> SUB"
    elif "Ridley Scott" in director:
        diagram += "    FIRE[Luz de Fuego/Velas] --> SUB\n    SIDE[Luz Lateral Natural] --> SUB"
    else:
        diagram += "    KEY[Luz Principal] --> SUB\n    FILL[Luz de Relleno] --> SUB\n    RIM[Luz de Recorte] --> SUB"

    json_output = {
        "cinematógrafo": "Asistente IMAX Antigravity V2",
        "tipo_de_toma": angle_name,
        "motor_optimizado": engine,
        "descripcion": scene,
        "datos_de_consistencia": {
            "rasgos_personaje": character,
            "vestuario": wardrobe,
            "paleta_color": color
        },
        "stack_tecnico": {
            "formato": "IMAX 70mm (15-perf)",
            "lente": lens,
            "pelicula": stock,
            "relacion_aspecto": aspect_ratio
        },
        "intencion_director": director,
        "esquema_iluminacion": diagram,
        "prompt_final": full_prompt
    }
    return json_output, full_prompt, diagram

def generate_intelligence(system_prompt, user_input, engine_choice="GPT-5.2"):
    """Lógica multicanal para análisis y razonamiento"""
    try:
        if engine_choice == "GPT-5.2":
            if "OPENAI_API_KEY" not in st.secrets:
                st.error("Falta OPENAI_API_KEY para activar GPT-5.2.")
                return None
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.responses.create(
                model="gpt-5.2",
                input=f"SYSTEM: {system_prompt}\nUSER: {user_input}"
            )
            return response.output_text
            
        elif engine_choice == "GPT-4o-mini (Fast)":
            if "OPENAI_API_KEY" not in st.secrets:
                st.error("Falta OPENAI_API_KEY.")
                return None
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ]
            )
            return response.choices[0].message.content
            
        elif engine_choice == "Gemini Flash (Free)":
            if "GOOGLE_API_KEY" not in st.secrets:
                st.error("Falta GOOGLE_API_KEY.")
                return None
            client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
            # Usando el modelo Flash para análisis de texto rápido/gratis
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=f"{system_prompt}\n\n{user_input}"
            )
            return response.text
            
    except Exception as e:
        error_msg = str(e)
        if "billing_hard_limit_reached" in error_msg or "insufficient_quota" in error_msg:
            st.error("⚠️ Límite de facturación alcanzado en el proveedor seleccionado.")
        else:
            st.error(f"Error en {engine_choice}: {error_msg}")
        return None

def analyze_audio_with_gemini(audio_file_path, char_desc, vibe, mime_type, duration_seconds=0):
    try:
        if "GOOGLE_API_KEY" not in st.secrets:
            st.error("Falta GOOGLE_API_KEY en los secretos de Streamlit.")
            return None
        
        # Usando la nueva librería google-genai para mayor robustez
        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
        
        # Subir archivo usando el nuevo SDK (Google Gen AI)
        with open(audio_file_path, "rb") as f:
            audio_file = client.files.upload(file=f, config={'mime_type': mime_type})
        
        # Duración legible para el prompt
        duration_info = f"Duration: {round(duration_seconds, 1)} seconds." if duration_seconds > 0 else ""
        
        prompt = f"""
        Analyze this audio ({duration_info}) and create a COMPREHENSIVE cinematographic storyboard that covers the ENTIRE timeline from start to finish.
        
        Character Context: {char_desc}
        Style/Vibe: {vibe}
        
        Mandatory Rules:
        1. Distribution: Spread shots evenly across the whole {duration_seconds}s. Do NOT stop after the first 60 seconds.
        2. Sequence: Provide as many shots as needed to represent the full emotional arc of the audio.
        3. For each shot, provide:
           - Timestamp (e.g., 0:05, 1:20, 2:45)
           - Scene Action (English)
           - Recommended Shot Type (English)
           - Mood/Atmosphere (English)
        
        Maintain absolute visual consistency for the character across all shots.
        Format the output clearly using markdown.
        """
        
        response = None
        # Probamos varios identificadores comunes para asegurar compatibilidad en 2026
        for model_id in ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-2.0-flash']:
            try:
                response = client.models.generate_content(
                    model=model_id,
                    contents=[prompt, audio_file]
                )
                if response: break
            except Exception as e_model:
                if "404" in str(e_model) or "not found" in str(e_model).lower():
                    continue
                else:
                    raise e_model
        
        if not response:
            return "Error: No se encontró un modelo de Gemini Flash compatible."
            
        return response.text
    except Exception as e:
        st.error(f"Error analizando audio con Gemini (SDK GenAI): {str(e)}")
        return None

def main():
    templates = TEMPLATES
    
    st.title("🎬 Asistente Cinematográfico PRO V2: IMAX Hub")
    st.subheader("Optimización de Prompts Cinematográficos (Sin Generadores de Imágenes)")
    
    tabs = st.tabs(["🎮 Panel de Control", "📜 Analizador de Guion", "🎵 Ritmo & Audio (Storyboard)"])
    
    with st.sidebar:
        st.write("### 🧠 Inteligencia Maestra")
        intel_choice = st.selectbox("Motor de Razonamiento:", ["GPT-5.2", "GPT-4o-mini (Fast)", "Gemini Flash (Free)"], index=0)
        
        st.write("### 🎥 Cámara y Estilo")
        director_style_keys = list(templates['director_styles'].keys())
        director_choice = st.selectbox("Firma Visual del Director:", director_style_keys)
        
        lens_presets_keys = list(templates['lens_presets'].keys())
        lens_choice = st.selectbox("Características del Lente:", lens_presets_keys)
        
        stock_choice = st.selectbox("Tipo de Película (Stock):", templates['film_stocks'])
        
        color_palettes_keys = list(templates['color_palettes'].keys())
        color_choice = st.selectbox("Paleta de Color:", color_palettes_keys)
        
        st.write("### 🚀 Motor de IA Destino")
        engine_choice = st.selectbox("Optimizar para:", ["Meta AI / Grok", "Midjourney", "DALL-E 3", "Qwen / Flux"])

    with tabs[0]:
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            st.write("### 👥 Escena y Consistencia de Personaje")
            scene_desc = st.text_area("Entorno de la Escena:", placeholder="Una estación espacial abandonada orbitando un sol moribundo...", key="scene_creator")
            char_desc = st.text_area("Perfil del Personaje (Rasgos constantes):", placeholder="Un veterano curtido con un brazo mecánico y barba blanca.", key="char_creator")
            wardrobe_desc = st.text_input("Detalles del Vestuario:", placeholder="Traje de vuelo desgastado con insignias remendadas.", key="wardrobe_creator")
            
            st.write("### 📸 Ángulos de Cámara")
            shot_angles_keys = list(templates['shot_angles'].keys())
            selected_angles = st.multiselect("Selecciona ángulos para la lista de tomas:", shot_angles_keys, default=["Plano General (WS)", "Primer Plano (CU)"], key="angles_creator")

            if st.button("🎬 ACCIÓN: Generar Lista de Tomas"):
                if not scene_desc or not char_desc:
                    st.error("Por favor, proporciona descripciones de la escena y del personaje.")
                else:
                    results = []
                    for angle in selected_angles:
                        json_res, prompt_res, diag_res = generate_prompt(
                            scene_desc, 
                            char_desc,
                            wardrobe_desc,
                            templates['color_palettes'][color_choice],
                            templates['director_styles'][director_choice],
                            lens_choice,
                            stock_choice,
                            angle,
                            templates['shot_angles'][angle],
                            engine_choice
                        )
                        results.append((json_res, prompt_res, diag_res))
                    st.session_state['shot_list_v2'] = results

        with col2:
            st.write("### 💎 Salida Cinematográfica (V2)")
            if 'shot_list_v2' in st.session_state:
                for i, (json_res, prompt_res, diag_res) in enumerate(st.session_state['shot_list_v2']):
                    with st.expander(f"Toma {i+1}: {json_res['tipo_de_toma']} ({engine_choice})", expanded=(i==0)):
                        st.write("#### 🚀 Prompt Optimizado (Copia esto)")
                        st.text_area(f"Prompt {i+1}:", value=prompt_res, height=120, key=f"p_v2_{i}")
                        st.write("---")
                        # Image generation removed per user request
                
                st.info("💡 **Tip:** Copia el prompt en tu generador de imágenes favorito (Midjourney, DALL-E, Flux, etc.)")
            else:
                st.write("Completa los detalles y elige un Director Maestro para generar tus tomas.")

    with tabs[1]:
        st.write("### 🖊️ Pegar Fragmento de Guion")
        script_text = st.text_area("Fragmento del Guion (Acción y Diálogos):", placeholder="EXT. ESTACIÓN ESPACIAL - ATARDECER\nMax está frente a la esclusa, mirando al abismo. Suspira, su brazo metálico brilla...", height=200)
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            parser_char = st.text_input("Ancla de Identidad del Personaje:", placeholder="Max, el veterano curtido")
        with col_c2:
            parser_wardrobe = st.text_input("Ancla de Vestuario:", placeholder="Traje de vuelo andrajoso")

        if st.button("🔨 ANALIZAR GUION Y CREAR TOMAS"):
            if not script_text or not parser_char:
                st.error("Por favor, proporciona el texto del guion e identidad del personaje.")
            else:
                if intel_choice:
                    with st.spinner(f"{intel_choice} analizando subtexto y narrativa visual..."):
                        system_instr = "Eres un Director de Fotografía experto. Analiza el guion y devuelve UNA LISTA de hasta 5 momentos clave. Para cada momento, describe la acción en una frase. Sé técnico y preciso."
                        analysis = generate_intelligence(system_instr, f"Guion: {script_text}", intel_choice)
                        if analysis:
                            # Parsear la lista (asumiendo formato de lista)
                            moments = [m.strip() for m in analysis.split('\n') if len(m.strip()) > 5][:5]
                        else:
                            moments = [line.strip() for line in script_text.split('.') if len(line.strip()) > 10][:5]
                else:
                    # Simple logic to simulate "parsing" key moments
                    moments = [line.strip() for line in script_text.split('.') if len(line.strip()) > 10][:5]
                
                if not moments: moments = [script_text[:100]] # Fallback
                
                # Assign angles based on keywords or cycle
                shot_angles_keys_list = list(templates['shot_angles'].keys())
                results = []
                for i, moment in enumerate(moments): 
                    angle = shot_angles_keys_list[i % len(shot_angles_keys_list)]
                    json_res, prompt_res, diag_res = generate_prompt(
                        moment, 
                        parser_char,
                        parser_wardrobe,
                        templates['color_palettes'][color_choice],
                        templates['director_styles'][director_choice],
                        lens_choice,
                        stock_choice,
                        angle,
                        templates['shot_angles'][angle],
                        engine_choice
                    )
                    results.append((json_res, prompt_res, diag_res))
                st.session_state['parsed_list'] = results

        if 'parsed_list' in st.session_state:
            st.write("### 🎬 Lista de Tomas Derivada del Guion")
            for i, (json_res, prompt_res, diag_res) in enumerate(st.session_state['parsed_list']):
                with st.expander(f"Momento de Escena {i+1}: {json_res['tipo_de_toma']}", expanded=(i==0)):
                    st.write(f"**Acción:** *{json_res['descripcion']}*")
                    
                    # Botón de carga rápida
                    if st.button(f"📋 Cargar Toma {i+1} en Panel", key=f"btn_copy_{i}"):
                        st.session_state['scene_creator'] = json_res['descripcion']
                        st.session_state['char_creator'] = parser_char
                        st.session_state['wardrobe_creator'] = parser_wardrobe
                        st.success(f"¡Toma {i+1} cargada satisfactoriamente! Ve a la pestaña 'Panel de Control'.")
                        st.rerun()

                    st.text_area(f"Prompt Optimizado {i+1}:", value=prompt_res, height=100, key=f"ps_{i}")

    with tabs[2]:
        st.write("### 🎵 Generador de Storyboard por Ritmo")
        st.info("Sube una canción o audio para generar un storyboard sincronizado con el tempo.")
        
        uploaded_audio = st.file_uploader("Sube tu archivo de audio (mp3, wav)", type=["mp3", "wav"])
        audio_char = st.text_input("Protagonista para el Storyboard:", placeholder="Un cosmonauta perdido en Marte")
        
        if uploaded_audio and st.button("🔥 GENERAR STORYBOARD SINCRONIZADO"):
            with st.spinner("Analizando ritmo y narrativa..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_audio.name[uploaded_audio.name.rfind('.'):]) as tmp:
                    tmp.write(uploaded_audio.getbuffer())
                    tmp_path = tmp.name
                
                try:
                    # 1. Librosa BPM & Duration Analysis
                    y, sr = librosa.load(tmp_path)
                    duration_secs = librosa.get_duration(y=y, sr=sr)
                    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
                    bpm = float(np.mean(tempo))
                    st.success(f"Track Detectado: {round(bpm, 1)} BPM | Duración: {round(duration_secs, 1)}s")
                    
                    # 2. Gemini Analysis
                    storyboard_text = analyze_audio_with_gemini(tmp_path, audio_char, director_choice, uploaded_audio.type, duration_secs)
                    
                    if storyboard_text:
                        st.session_state['audio_storyboard'] = storyboard_text
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
        
        if 'audio_storyboard' in st.session_state:
            st.write("### 📝 Storyboard Producido")
            st.markdown(st.session_state['audio_storyboard'])
            
            st.write("---")
            st.caption("Tip: Puedes copiar estas descripciones al Panel de Control para generar los prompts técnicos finales.")

if __name__ == "__main__":
    main()
