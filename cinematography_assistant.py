import streamlit as st
import json
import os

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

def generate_prompt(scene, character, wardrobe, color, director, lens, stock, angle_name, angle_desc):
    # Technical mapping
    is_anamorphic = "Anamorphic" in lens
    aspect_ratio = "2.76:1 (Ultra Panavision)" if is_anamorphic else "1.43:1 (IMAX Full)"
    
    technical_details = f"Shot on IMAX MSM 9802 15/70mm film, {lens} lenses, {stock} film stock. Aspect ratio {aspect_ratio}."
    
    # Consistency Anchors
    consistency_block = f"Character: {character}. Wardrobe: {wardrobe}. Color Palette: {color}."
    
    full_prompt = (
        f"{angle_name}: {scene}. {angle_desc}. {consistency_block}. {director}. {technical_details}. "
        f"Key visual traits: {'oval bokeh, horizontal lens flares, ' if is_anamorphic else ''}"
        f"extreme detail, naturalistic grain, high dynamic range, 12k resolution texture, visceral atmosphere."
    )
    
    json_output = {
        "cinematographer": "Antigravity IMAX Assistant",
        "shot_type": angle_name,
        "description": scene,
        "consistency_data": {
            "character_traits": character,
            "wardrobe": wardrobe,
            "color_palette": color
        },
        "technical_stack": {
            "format": "IMAX 70mm (15-perf)",
            "lens": lens,
            "stock": stock,
            "aspect_ratio": aspect_ratio
        },
        "director_intent": director,
        "final_prompt": full_prompt
    }
    return json_output, full_prompt

def main():
    templates = load_templates()
    
    st.title("🎬 Assistant Cinematographique PRO: IMAX 70mm")
    st.subheader("Consistent characters & multi-angle shot lists")
    
    with st.sidebar:
        st.write("### 🎥 Camera & Style")
        director_choice = st.selectbox("Director Visual Style:", list(templates['director_styles'].keys()))
        lens_choice = st.selectbox("Lens Characteristics:", list(templates['lens_presets'].keys()))
        stock_choice = st.selectbox("Film Stock:", templates['film_stocks'])
        color_choice = st.selectbox("Color Palette:", list(templates['color_palettes'].keys()))

    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.write("### 👥 Scene & Character Consistency")
        scene_desc = st.text_area("Scene Setting (Environment):", placeholder="An abandoned space station orbiting a dying sun...")
        char_desc = st.text_area("Character Profile (Consistent traits):", placeholder="A grizzled veteran with a mechanical arm and white beard.")
        wardrobe_desc = st.text_input("Wardrobe Details:", placeholder="Worn flight suit with patched insignia.")
        
        st.write("### 📸 Shot Angles")
        selected_angles = st.multiselect("Select angles for the shot list:", list(templates['shot_angles'].keys()), default=["Wide Shot (WS)", "Close-Up (CU)"])

        if st.button("🎬 ACTION: Generate Shot List"):
            if not scene_desc or not char_desc:
                st.error("Please provide both scene and character descriptions.")
            else:
                results = []
                for angle in selected_angles:
                    json_res, prompt_res = generate_prompt(
                        scene_desc, 
                        char_desc,
                        wardrobe_desc,
                        templates['color_palettes'][color_choice],
                        templates['director_styles'][director_choice],
                        lens_choice,
                        stock_choice,
                        angle,
                        templates['shot_angles'][angle]
                    )
                    results.append((json_res, prompt_res))
                st.session_state['shot_list'] = results

    with col2:
        st.write("### 💎 Cinematic Shot List")
        if 'shot_list' in st.session_state:
            for i, (json_res, prompt_res) in enumerate(st.session_state['shot_list']):
                with st.expander(f"Shot {i+1}: {json_res['shot_type']}", expanded=(i==0)):
                    st.write("#### 🚀 Prompt")
                    st.text_area(f"Prompt {i+1}:", value=prompt_res, height=120, key=f"p_{i}")
                    st.write("#### 📝 JSON Data")
                    st.code(json.dumps(json_res, indent=2), language="json")
            
            st.info("💡 **Consistency Tip:** Copy the 'Character Profile' exactly for all image generator iterations to maintain face/body traits.")
        else:
            st.write("Fill in the scene and character details to generate your cinematic shot list.")

if __name__ == "__main__":
    main()
