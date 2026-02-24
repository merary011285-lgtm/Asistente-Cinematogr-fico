import streamlit as st
import json
import os
import replicate
from openai import OpenAI
import google.generativeai as st_genai # Older library for other uses if any
from google import genai # New library for Imagen 3
import fal_client
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

def load_templates():
    with open('prompt_templates.json', 'r') as f:
        return json.load(f)

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

def generate_image_replicate(prompt):
    try:
        if "REPLICATE_API_TOKEN" not in st.secrets:
            st.error("Falta REPLICATE_API_TOKEN en los secretos de Streamlit o variables de entorno.")
            return None
        
        # Usando Flux.1 [dev] por defecto para calidad cinematográfica
        output = replicate.run(
            "black-forest-labs/flux-dev",
            input={
                "prompt": prompt,
                "aspect_ratio": "16:9",
                "guidance_scale": 3.5,
                "num_inference_steps": 28
            }
        )
        # Flux suele devolver una lista de URLs o un iterador
        if isinstance(output, list):
            return output[0]
        return output
    except Exception as e:
        st.error(f"Error con Replicate: {str(e)}")
        return None

def generate_image_openai(prompt):
    try:
        if "OPENAI_API_KEY" not in st.secrets:
            st.error("Falta OPENAI_API_KEY en los secretos de Streamlit.")
            return None
        
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="hd",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        error_msg = str(e)
        if "billing_hard_limit_reached" in error_msg or "insufficient_quota" in error_msg:
            st.error("⚠️ **Límite de Facturación en OpenAI Alcanzado.**\n\nNo te preocupes, puedes seguir trabajando usando los otros motores:\n- Selecciona **🔥 Gemini (Imagen 3)** (si tienes créditos de Google).\n- Selecciona **🔥 Fal.ai (Flux)** (si tienes créditos en Fal.ai).")
        else:
            st.error(f"Error con OpenAI: {error_msg}")
        return None

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

def generate_image_gemini(prompt):
    try:
        if "GOOGLE_API_KEY" not in st.secrets:
            st.error("Falta GOOGLE_API_KEY en los secretos de Streamlit.")
            return None
        
        # Usando la nueva librería google-genai para Imagen 3 (Ojo: es plural generate_images)
        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
        response = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt=prompt,
            config={
                'number_of_images': 1,
                'aspect_ratio': '16:9',
                'safety_filter_level': 'block_only_high'
            }
        )
        # La respuesta en google-genai contiene una lista de imágenes
        if response.generated_images:
            # En la versión más reciente, es generated_images[0].image_url o .image_resource.url
            try:
                return response.generated_images[0].image_url
            except AttributeError:
                return response.generated_images[0].image_resource.url
        return None
    except Exception as e:
        # Fallback o error detallado
        st.error(f"Error con Gemini Imagen 3: {str(e)}")
        # Intentar con st_genai si es necesario, pero Imagen 3 es mejor en google-genai
        return None

def generate_image_fal(prompt):
    try:
        if "FAL_KEY" not in st.secrets:
            st.error("Falta FAL_KEY en los secretos de Streamlit.")
            return None
        
        # Usamos Flux.1 [dev] via fal-client (el famoso 'Flow')
        handler = fal_client.submit(
            "fal-ai/flux/dev",
            arguments={
                "prompt": prompt,
                "image_size": "landscape_16_9"
            },
        )
        result = handler.get()
        if "images" in result and result["images"]:
            return result["images"][0]["url"]
        return None
    except Exception as e:
        error_msg = str(e)
        if "Exhausted balance" in error_msg or "locked" in error_msg.lower():
            st.error("⚠️ **Saldo Agotado en Fal.ai.**\n\nTu cuenta de Fal.ai no tiene créditos suficientes.\n\n**Solución**: \n- Selecciona **🔥 Gemini (Imagen 3)** (Google).\n- Selecciona **🔥 Replicate (Flux)** (si tienes saldo en Replicate).")
        else:
            st.error(f"Error con Fal.ai: {error_msg}")
        return None

def analyze_audio_with_gemini(audio_file_path, char_desc, vibe, mime_type):
    try:
        if "GOOGLE_API_KEY" not in st.secrets:
            st.error("Falta GOOGLE_API_KEY en los secretos de Streamlit.")
            return None
        
        # Usando la nueva librería google-genai para mayor robustez
        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
        
        # Subir archivo usando el nuevo SDK (Google Gen AI)
        # Especificamos el mime_type porque el SDK no siempre lo detecta en archivos temporales
        with open(audio_file_path, "rb") as f:
            audio_file = client.files.upload(file=f, config={'mime_type': mime_type})
        
        prompt = f"""
        Analyze this audio and create a detailed cinematographic storyboard.
        Character Context: {char_desc}
        Style/Vibe: {vibe}
        
        Output a 5-shot storyboard (or more if long) with timestamps every 5-10 seconds.
        For each shot, provide:
        - Timestamp (e.g., 0:05)
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
    templates = load_templates()
    
    st.title("🎬 Asistente Cinematográfico PRO V2: IMAX Hub")
    st.subheader("Firmas de Directores Maestros y Optimización Multi-Motor")
    
    tabs = st.tabs(["🎮 Panel de Control", "📜 Analizador de Guion", "🎵 Ritmo & Audio (Storyboard)"])
    
    with st.sidebar:
        st.write("### 🧠 Inteligencia Maestra")
        intel_choice = st.selectbox("Motor de Razonamiento:", ["GPT-5.2", "GPT-4o-mini (Fast)", "Gemini Flash (Free)"], index=0)
        
        st.write("### 🎥 Cámara y Estilo")
        director_choice = st.selectbox("Firma Visual del Director:", list(templates['director_styles'].keys()))
        lens_choice = st.selectbox("Características del Lente:", list(templates['lens_presets'].keys()))
        stock_choice = st.selectbox("Tipo de Película (Stock):", templates['film_stocks'])
        color_choice = st.selectbox("Paleta de Color:", list(templates['color_palettes'].keys()))
        
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
            selected_angles = st.multiselect("Selecciona ángulos para la lista de tomas:", list(templates['shot_angles'].keys()), default=["Plano General (WS)", "Primer Plano (CU)"], key="angles_creator")

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
                        
                        st.write("#### 💡 Esquema de Iluminación (Diagrama)")
                        st.code(diag_res, language="mermaid")
                        st.info("Copia el código de arriba en un editor Mermaid para ver el diagrama visual.")
                        
                        st.write("#### 📝 Metadatos JSON")
                        st.code(json.dumps(json_res, indent=2, ensure_ascii=False), language="json")
                        
                        st.write("---")
                        st.write("#### 🎨 Generación de Imagen Directa")
                        
                        btn_key_base = f"gen_btn_{i}_{engine_choice}"
                        
                        # Detectamos qué llaves están presentes
                        has_openai = "OPENAI_API_KEY" in st.secrets
                        has_gemini = "GOOGLE_API_KEY" in st.secrets
                        has_fal = "FAL_KEY" in st.secrets
                        has_replicate = "REPLICATE_API_TOKEN" in st.secrets
                        
                        if not any([has_openai, has_gemini, has_fal, has_replicate]):
                            st.warning("⚠️ No se detectaron llaves de API. Configura `.streamlit/secrets.toml` para habilitar la generación.")
                        else:
                            st.info("Elige el proveedor según tus créditos disponibles:")
                            cols = st.columns(4)
                            
                            if has_openai:
                                if cols[0].button("🚀 DALL-E 3", key=f"{btn_key_base}_oa"):
                                    with st.spinner("Generando en DALL-E 3..."):
                                        img_url = generate_image_openai(prompt_res)
                                        if img_url: st.image(img_url, caption="Resultado DALL-E 3")
                            
                            if has_gemini:
                                if cols[1].button("♊ Gemini/Imagen", key=f"{btn_key_base}_gem"):
                                    with st.spinner("Generando en Imagen 3..."):
                                        img_url = generate_image_gemini(prompt_res)
                                        if img_url: st.image(img_url, caption="Resultado Imagen 3")

                            if has_fal:
                                if cols[2].button("🔥 Fal.ai (Flux)", key=f"{btn_key_base}_fal"):
                                    with st.spinner("Generando en Fal.ai (Flux)..."):
                                        img_url = generate_image_fal(prompt_res)
                                        if img_url: st.image(img_url, caption="Resultado Fal/Flux")

                            if has_replicate:
                                if cols[3].button("🌀 Replicate", key=f"{btn_key_base}_repl"):
                                    with st.spinner("Generando en Replicate..."):
                                        img_url = generate_image_replicate(prompt_res)
                                        if img_url: st.image(img_url, caption="Resultado Replicate")
                
                st.info("💡 **Tip de Fase 2:** El prompt ahora incluye modificadores técnicos específicos para el motor de IA seleccionado.")
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
                            moments = [line.strip() for line in script_text.split('.') if len(line.strip()) > 10]
                else:
                    # Simple logic to simulate "parsing" key moments (split by sentences or common script markers)
                    moments = [line.strip() for line in script_text.split('.') if len(line.strip()) > 10]
                
                if not moments: moments = [script_text[:100]] # Fallback
                
                # Assign angles based on keywords or cycle
                angle_list = list(templates['shot_angles'].keys())
                results = []
                for i, moment in enumerate(moments[:5]): # Limit to first 5 moments for demo
                    angle = angle_list[i % len(angle_list)]
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
                    
                    # Botón de carga rápida (Solicitado por el usuario)
                    if st.button(f"📋 Cargar Toma {i+1} en Panel (Pega esto)", key=f"btn_copy_{i}"):
                        st.session_state['scene_creator'] = json_res['descripcion']
                        st.session_state['char_creator'] = json_res['personaje']
                        st.session_state['wardrobe_creator'] = json_res['vestuario']
                        st.success(f"¡Toma {i+1} cargada satisfactoriamente! Ve a la pestaña 'Panel de Control'.")
                        st.rerun()

                    st.text_area(f"Prompt Optimizado {i+1}:", value=prompt_res, height=100, key=f"ps_{i}")
                    st.code(diag_res, language="mermaid")

    with tabs[2]:
        st.write("### 🎵 Generador de Storyboard por Ritmo")
        st.info("Sube una canción o audio para generar un storyboard sincronizado con el tempo y la letra.")
        
        uploaded_audio = st.file_uploader("Sube tu archivo de audio (mp3, wav)", type=["mp3", "wav"])
        audio_char = st.text_input("Protagonista para el Storyboard:", placeholder="Un cosmonauta perdido en Marte")
        
        if uploaded_audio and st.button("🔥 GENERAR STORYBOARD SINCRONIZADO"):
            with st.spinner("Analizando ritmo y narrativa..."):
                # Save temp file for processing
                with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_audio.name[uploaded_audio.name.rfind('.'):]) as tmp:
                    tmp.write(uploaded_audio.getbuffer())
                    tmp_path = tmp.name
                
                try:
                    # 1. Librosa BPM Analysis
                    y, sr = librosa.load(tmp_path)
                    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
                    # Convertimos a scalar si es un array (común en nuevas versiones de librosa)
                    bpm = float(np.mean(tempo))
                    st.success(f"Tempo Detectado: {round(bpm, 1)} BPM")
                    
                    # 2. Gemini Analysis
                    storyboard_text = analyze_audio_with_gemini(tmp_path, audio_char, director_choice, uploaded_audio.type)
                    
                    if storyboard_text:
                        st.session_state['audio_storyboard'] = storyboard_text
                        st.session_state['audio_bpm'] = tempo
                finally:
                    # Clean up
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
        
        if 'audio_storyboard' in st.session_state:
            st.write("### 📝 Storyboard Producido")
            st.markdown(st.session_state['audio_storyboard'])
            
            st.write("---")
            st.caption("Tip: Puedes copiar estas descripciones al Panel de Control para generar los prompts técnicos finales.")

if __name__ == "__main__":
    main()
