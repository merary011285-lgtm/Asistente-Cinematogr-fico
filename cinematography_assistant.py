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
  "camera_movements": {
    "Estático (Fixed)": "Stable static camera, no movement, focus on composition.",
    "Dolly In (Acercamiento)": "Slow dolly-in movement towards the subject, increasing tension.",
    "Dolly Out (Alejamiento)": "Slow dolly-out movement away from the subject, revealing the environment.",
    "Panorámica (Panning)": "Horizontal pan movement, scanning the horizon.",
    "Tilt Up (Inclinación Arriba)": "Vertical tilt up movement, looking towards the sky or heights.",
    "Tilt Down (Inclinación Abajo)": "Vertical tilt down movement, looking towards the ground.",
    "Tracking Shot (Seguimiento)": "Lateral tracking shot following the character's movement.",
    "Grúa (Crane Shot)": "High-angle crane shot, sweeping vertical and horizontal movement.",
    "Handheld (Cámara en Mano)": "Visceral handheld camera, organic shaky movement, documentary feel.",
    "Zoom In (Digital/Óptico)": "Intense zoom-in on details or emotions.",
    "Orbit (Circular)": "Circular tracking shot orbiting the subject 360 degrees."
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
    "Plano Americano (Cowboy)": "Waist up to mid-thigh, traditional western style shot.",
    "Plano Medio (MS)": "Waist up, focusing on interaction and wardrobe detail.",
    "Plano Medio Corto (MCU)": "Chest up, focusing on facial expressions and posture.",
    "Primer Plano (CU)": "Tight on face, shallow depth of field, intense 70mm skin texture.",
    "Primerísimo Primer Plano (ECU)": "Extreme tight shot on eyes or mouth, focusing on intense emotion.",
    "Plano Detalle (XCU)": "Tiny detail of an object or texture, hyper-focused.",
    "Ángulo Picado": "Looking down at the subject, making them appear vulnerable.",
    "Ángulo Contrapicado (Heroico)": "Looking up at character, making them appear powerful.",
    "Cenital / Vista de Pájaro": "Looking down, showing isolation or objective perspective.",
    "Ángulo Nadir": "Looking straight up from the ground, extreme low angle.",
    "Ángulo Holandés (Tensión)": "Tilted horizon, creating tension and unease.",
    "Plano de Perfil": "Side profile of the subject, highlighting silhouette and features."
  },
  "color_palettes": {
    "Clásico Teal & Orange": "Cool shadows, warm skin tones, high dynamic range pop.",
    "Desaturado / Bleach Bypass": "High contrast, gritty, muted colors, metallic feel.",
    "Tecnicolor Heredado": "Deep reds and blues, high saturation, nostalgic 1950s epic feel.",
    "Monocromo (Double-X)": "Hyper-detailed black and white, deep blacks, glowing silver highlights.",
    "Neón Noir": "Vibrant pinks and cyans against deep darkness."
  }
}

def generate_prompt(scene, character, wardrobe, color, director, lens, stock, movement, angle_name, angle_desc, engine):
    # Mapping técnico
    is_anamorphic = "Anamórfico" in lens or "Anamorphic" in lens
    aspect_ratio = "2.76:1 (Ultra Panavision)" if is_anamorphic else "1.43:1 (IMAX Full)"
    
    technical_details = f"Shot on IMAX MSM 9802 15/70mm film, {lens} lenses, {stock} film stock. Aspect ratio {aspect_ratio}."
    
    # Anclas de Consistencia Blindada (EN)
    # Forced visual consistency for image generators
    consistency_block = (
        f"CHARACTER CONTINUITY: {character}. "
        f"WARDROBE CONSISTENCY: {wardrobe}. "
        f"COLOR SCHEME: {color}. "
        "Maintain identical facial features and identical clothing textures across shots."
    )
    
    # Optimización del Motor
    engine_suffix = ""
    if engine == "Midjourney":
        ratio = "2.76:1" if is_anamorphic else "1.43:1"
        engine_suffix = f" --ar {ratio} --v 6 --stylize 250"
    elif engine == "DALL-E 3":
        engine_suffix = " Wide-screen cinematic mode, hyper-photorealistic, maintain exact visual continuity with previous frames."

    # Prompt final (Totalmente en Inglés)
    full_prompt = (
        f"{angle_name}: {scene}. {angle_desc}. Camera Movement: {movement}. "
        f"{consistency_block} {director}. {technical_details}. "
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
        "movimiento": movement,
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
        Analyze this audio ({duration_info}) and create a COMPREHENSIVE cinematographic storyboard.
        
        MANDATORY STEP 1: PRODUCTION BIBLE
        Based on the lyrics, rhythm, and vibe, detect and define:
        - LOCATION: Where is this taking place?
        - CHARACTER: Who is the protagonist? (Physical traits)
        - WARDROBE: What are they wearing?
        - EPOCH: When is this happening? (Past, Present, Future, Specific Year)
        
        MANDATORY STEP 2: STORYBOARD SEQUENCE
        Create a sequence of shots covering the entire {duration_seconds}s.
        For each shot, provide:
        - Timestamp (e.g., 0:05)
        - Scene Action (Technical English)
        - Shot Type & Angle (Technical English)
        - Mood/Atmosphere
        
        FORMATTING RULE:
        Start your response with a JSON-like block for the PRODUCTION BIBLE so I can parse it, then follow with the Markdown Storyboard.
        Example:
        ---PRODUCTION_BIBLE---
        LOCATION: [Value]
        CHARACTER: [Value]
        WARDROBE: [Value]
        EPOCH: [Value]
        ---END_BIBLE---
        
        Maintain absolute visual consistency across all shots based on the PRODUCTION BIBLE.
        """
        
        response = None
        # Probamos varios identificadores comunes para asegurar compatibilidad en 2026
        for model_id in ['gemini-2.0-flash', 'gemini-1.5-flash-latest', 'gemini-1.5-flash']:
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
        st.write("### 🛡️ Master de Continuidad")
        st.info("Define aquí los rasgos persistentes para todo el proyecto.")
        
        # Centralized consistency state
        shared_char = st.text_area("Ancla: Personaje (Físico):", 
                                   value=st.session_state.get('char_master', "Un veterano curtido con brazo mecánico"),
                                   key="char_master_input")
        shared_wardrobe = st.text_input("Ancla: Vestuario:", 
                                        value=st.session_state.get('wardrobe_master', "Traje de vuelo desgastado"),
                                        key="wardrobe_master_input")
        
        st.session_state['char_master'] = shared_char
        st.session_state['wardrobe_master'] = shared_wardrobe

        st.write("---")
        st.write("### 🧠 Inteligencia Maestra")
        intel_choice = st.selectbox("Motor de Razonamiento:", ["GPT-4o-mini (Fast)", "GPT-5.2", "Gemini Flash (Free)"], index=0)
        
        st.write("### 🎥 Cámara y Estilo")
        # Use direct dict access from TEMPLATES to satisfy linter
        director_choice = st.selectbox("Firma Visual del Director:", list(TEMPLATES["director_styles"].keys()))
        lens_choice = st.selectbox("Características del Lente:", list(TEMPLATES["lens_presets"].keys()))
        movement_choice = st.selectbox("Movimiento de Cámara:", list(TEMPLATES["camera_movements"].keys()))
        stock_choice = st.selectbox("Tipo de Película (Stock):", list(TEMPLATES['film_stocks']))
        color_choice = st.selectbox("Paleta de Color:", list(TEMPLATES["color_palettes"].keys()))
        
        st.write("### 🚀 Motor de IA Destino")
        engine_choice = st.selectbox("Optimizar para:", ["Meta AI / Grok", "Midjourney", "DALL-E 3", "Qwen / Flux"])

    with tabs[0]:
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            st.write("### 👥 Escena y Acción Local")
            scene_desc = st.text_area("Entorno de la Escena:", placeholder="Una estación espacial abandonada orbitando un sol moribundo...", key="scene_creator")
            
            # Using master consistency states
            st.write(f"**Ancla Personaje:** `{st.session_state['char_master']}`")
            st.write(f"**Ancla Vestuario:** `{st.session_state['wardrobe_master']}`")
            
            char_desc = st.session_state['char_master']
            wardrobe_desc = st.session_state['wardrobe_master']
            
            st.write("### 📸 Ángulos de Cámara")
            shot_angles_keys = list(TEMPLATES['shot_angles'].keys())
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
                            templates['camera_movements'][movement_choice],
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
                    with st.expander(f"Toma {i+1}: {json_res['tipo_de_toma']} | {json_res['movimiento']} ({engine_choice})", expanded=(i==0)):
                        st.write("#### 🚀 Prompt Optimizado")
                        st.text_area(f"Prompt {i+1}:", value=prompt_res, height=120, key=f"p_v2_{i}")
                        
                        # Optimized prompt display with built-in copy button
                        st.code(prompt_res, language=None)
                        st.info("💡 Haz clic en el botón de la esquina superior derecha del cuadro gris para copiar.")

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
                    with st.spinner(f"{intel_choice} analizando subtexto y persistencia visual..."):
                        system_instr = """Eres un Director de Fotografía experto y Jefe de Continuidad. 
                        Analiza el guion y devuelve UNA LISTA de hasta 5 momentos clave.
                        
                        REGLA DE ORO DE CONTINUIDAD:
                        Para cada momento, debes mantener la descripción del personaje y vestuario EXACTAMENTE igual a lo detectado inicialmente en el fragmento.
                        
                        Devuelve: 
                        1. Descripción de la acción (en una frase técnica).
                        2. Rasgos físicos del personaje (persiste en cada toma).
                        3. Detalles del vestuario (persiste en cada toma).
                        
                        Formato: Acción | Personaje | Vestuario"""
                        
                        analysis = generate_intelligence(system_instr, f"Guion: {script_text}", intel_choice)
                        if analysis:
                            # Parsear la lista mejorada
                            moments_data = []
                            for line in analysis.split('\n'):
                                if '|' in line:
                                    parts = line.split('|')
                                    if len(parts) >= 3:
                                        moments_data.append({
                                            'action': parts[0].strip(),
                                            'char': parts[1].strip(),
                                            'wardrobe': parts[2].strip()
                                        })
                            moments = moments_data[:5]
                        else:
                            # Fallback simple
                            moments = [{'action': line.strip(), 'char': parser_char, 'wardrobe': parser_wardrobe} 
                                      for line in script_text.split('.') if len(line.strip()) > 10][:5]
                else:
                    # Simple logic to simulate "parsing" key moments
                    moments = [line.strip() for line in script_text.split('.') if len(line.strip()) > 10][:5]
                
                if not moments: moments = [script_text[:100]] # Fallback
                
                # Assign angles based on keywords or cycle
                shot_angles_keys_list = list(TEMPLATES['shot_angles'].keys())
                results = []
                for i, m_data in enumerate(moments): 
                    # Type checking to satisfy linter
                    if not isinstance(m_data, dict): continue
                    
                    angle_idx = int(i % len(shot_angles_keys_list))
                    angle = shot_angles_keys_list[angle_idx]
                    
                    json_res, prompt_res, diag_res = generate_prompt(
                        m_data.get('action', ''), 
                        m_data.get('char', ''),
                        m_data.get('wardrobe', ''),
                        TEMPLATES['color_palettes'][color_choice],
                        TEMPLATES['director_styles'][director_choice],
                        lens_choice,
                        stock_choice,
                        TEMPLATES['camera_movements'][movement_choice],
                        angle,
                        TEMPLATES['shot_angles'][angle],
                        engine_choice
                    )
                    results.append((json_res, prompt_res, diag_res))
                st.session_state['parsed_list'] = results

        if 'parsed_list' in st.session_state:
            st.write("### 🎬 Lista de Tomas Derivada del Guion")
            for i, (json_res, prompt_res, diag_res) in enumerate(st.session_state['parsed_list']):
                with st.expander(f"Momento de Escena {i+1}: {json_res['tipo_de_toma']} | {json_res['movimiento']}", expanded=(i==0)):
                    st.write(f"**Acción:** *{json_res['descripcion']}*")
                    
                    # Botón de carga rápida (Sincronizado con Master)
                    if st.button(f"📋 Cargar Toma {i+1} en Panel", key=f"btn_copy_{i}"):
                        st.session_state['scene_creator'] = json_res['descripcion']
                        st.session_state['char_master'] = json_res['datos_de_consistencia']['rasgos_personaje']
                        st.session_state['wardrobe_master'] = json_res['datos_de_consistencia']['vestuario']
                        st.success(f"¡Toma {i+1} cargada satisfactoriamente! Los anclas de continuidad se han actualizado.")
                        st.rerun()

                    st.text_area(f"Prompt Optimizado {i+1}:", value=prompt_res, height=100, key=f"ps_{i}")
                    
                    # Copy block for script analyzer
                    st.code(prompt_res, language=None)

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
            st.write("### � Biblia de Producción & Storyboard")
            
            full_text = st.session_state['audio_storyboard']
            
            # Parsing the Production Bible
            bible_data = {}
            if "---PRODUCTION_BIBLE---" in full_text and "---END_BIBLE---" in full_text:
                try:
                    bible_part = full_text.split("---PRODUCTION_BIBLE---")[1].split("---END_BIBLE---")[0].strip()
                    for line in bible_part.split('\n'):
                        if ':' in line:
                            k, v = line.split(':', 1)
                            bible_data[k.strip().upper()] = v.strip()
                except Exception:
                    pass
            
            if bible_data:
                cols = st.columns(4)
                with cols[0]: st.metric("📍 Localización", bible_data.get('LOCATION', 'N/A'))
                with cols[1]: st.metric("👤 Personaje", bible_data.get('CHARACTER', 'N/A')[:20] + "...")
                with cols[2]: st.metric("👕 Vestuario", bible_data.get('WARDROBE', 'N/A')[:20] + "...")
                with cols[3]: st.metric("⏳ Época", bible_data.get('EPOCH', 'N/A'))
                
                if st.button("🔄 Sincronizar Biblia con Master de Continuidad"):
                    if 'CHARACTER' in bible_data: st.session_state['char_master'] = bible_data['CHARACTER']
                    if 'WARDROBE' in bible_data: st.session_state['wardrobe_master'] = bible_data['WARDROBE']
                    st.success("¡Continuidad sincronizada!")
                    st.rerun()
            
            st.write("---")
            # Remove the bible block from display to keep it clean if desired, or show it all
            display_text = full_text.split("---END_BIBLE---")[-1].strip() if "---END_BIBLE---" in full_text else full_text
            st.markdown(display_text)
            
            st.write("---")
            st.caption("Tip: Los detalles de personaje y vestuario detectados se pueden aplicar a todo el proyecto usando el botón de sincronización.")

if __name__ == "__main__":
    main()
