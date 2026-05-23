import streamlit as st
import requests
import i18n


def translate_text(text: str) -> str:
    return i18n.translate(text)


def translate_list(items):
    return i18n.translate_list(items)


def format_text(text: str, translate: bool = False) -> str:
    if translate:
        # when translate flag set, use Kiswahili
        i18n.set_locale('sw')
        return i18n.translate(text)
    return text


def render_result_card(result: dict, translate_output: bool):
    if result.get("disease_type") == "invalid_image":
        invalid_title = format_text("⚠️ Invalid Image", translate_output)
        invalid_message = format_text("Please upload a clear image of a plant leaf for accurate disease detection.", translate_output)

        st.markdown("<div class='result-card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='disease-title'>{invalid_title}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='color: #ff5722; font-size: 1.1em; margin-bottom: 1em;'>{invalid_message}</div>", unsafe_allow_html=True)

        if result.get("symptoms"):
            st.markdown(f"<div class='section-title'>{format_text('Issue', translate_output)}</div>", unsafe_allow_html=True)
            st.markdown("<ul class='symptom-list'>", unsafe_allow_html=True)
            for symptom in translate_list(result.get("symptoms", [])):
                st.markdown(f"<li>{symptom}</li>", unsafe_allow_html=True)
            st.markdown("</ul>", unsafe_allow_html=True)

        if result.get("treatment"):
            st.markdown(f"<div class='section-title'>{format_text('What to do', translate_output)}</div>", unsafe_allow_html=True)
            st.markdown("<ul class='treatment-list'>", unsafe_allow_html=True)
            for treat in translate_list(result.get("treatment", [])):
                st.markdown(f"<li>{treat}</li>", unsafe_allow_html=True)
            st.markdown("</ul>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
        return

    if result.get("disease_detected"):
        disease_name = result.get('disease_name', 'N/A')
        if translate_output and isinstance(disease_name, str):
            disease_name = translate_text(disease_name)

        st.markdown("<div class='result-card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='disease-title'>🦠 {disease_name}</div>", unsafe_allow_html=True)
        st.markdown(f"<span class='info-badge'>{format_text('Type', translate_output)}: {translate_text(result.get('disease_type', 'N/A')) if translate_output else result.get('disease_type', 'N/A')}</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='info-badge'>{format_text('Severity', translate_output)}: {translate_text(result.get('severity', 'N/A')) if translate_output else result.get('severity', 'N/A')}</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='info-badge'>{format_text('Confidence', translate_output)}: {result.get('confidence', 'N/A')}% </span>", unsafe_allow_html=True)

        st.markdown(f"<div class='section-title'>{format_text('Symptoms', translate_output)}</div>", unsafe_allow_html=True)
        st.markdown("<ul class='symptom-list'>", unsafe_allow_html=True)
        for symptom in translate_list(result.get('symptoms', [])):
            st.markdown(f"<li>{symptom}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)

        st.markdown(f"<div class='section-title'>{format_text('Possible Causes', translate_output)}</div>", unsafe_allow_html=True)
        st.markdown("<ul class='cause-list'>", unsafe_allow_html=True)
        for cause in translate_list(result.get('possible_causes', [])):
            st.markdown(f"<li>{cause}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)

        st.markdown(f"<div class='section-title'>{format_text('Treatment', translate_output)}</div>", unsafe_allow_html=True)
        st.markdown("<ul class='treatment-list'>", unsafe_allow_html=True)
        for treat in translate_list(result.get('treatment', [])):
            st.markdown(f"<li>{treat}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)

        chemicals = result.get("chemical_recommendations", [])
        if chemicals:
            translated_chemicals = translate_list(chemicals)
            disease_type = str(result.get('disease_type', '')).lower()
            disease_name_check = str(result.get('disease_name', '')).lower() if result.get('disease_name') else ''
            fungal_words = ['late blight', 'powdery mildew', 'anthracnose', 'brown spot', 'downy mildew', 'rust']
            if 'fungal' in disease_type or any(word in disease_name_check for word in fungal_words):
                primary_label = format_text('Primary fungicide', translate_output)
            else:
                primary_label = format_text('Primary chemical', translate_output)

            st.markdown(f"<div class='section-title'>{format_text('Recommended Chemicals', translate_output)}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-weight: 600; margin-bottom: 0.5em;'>{primary_label}: {translated_chemicals[0]}</div>", unsafe_allow_html=True)
            if len(translated_chemicals) > 1:
                st.markdown(f"<div>{format_text('Also recommended', translate_output)}:</div>", unsafe_allow_html=True)
                st.markdown("<ul class='treatment-list'>", unsafe_allow_html=True)
                for chemical in translated_chemicals[1:]:
                    st.markdown(f"<li>{chemical}</li>", unsafe_allow_html=True)
                st.markdown("</ul>", unsafe_allow_html=True)

        st.markdown(f"<div class='timestamp'>🕒 {result.get('analysis_timestamp', 'N/A')}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    healthy_title = format_text("✅ Healthy Leaf", translate_output)
    healthy_message = format_text("No disease detected in this leaf. The plant appears to be healthy!", translate_output)
    status_label = format_text("Status", translate_output)
    confidence_label = format_text("Confidence", translate_output)

    st.markdown("<div class='result-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='disease-title'>{healthy_title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color: #4caf50; font-size: 1.1em; margin-bottom: 1em;'>{healthy_message}</div>", unsafe_allow_html=True)
    st.markdown(f"<span class='info-badge'>{status_label}: {translate_text(result.get('disease_type', 'healthy')) if translate_output else result.get('disease_type', 'healthy')}</span>", unsafe_allow_html=True)
    st.markdown(f"<span class='info-badge'>{confidence_label}: {result.get('confidence', 'N/A')}%</span>", unsafe_allow_html=True)
    st.markdown(f"<div class='timestamp'>🕒 {result.get('analysis_timestamp', 'N/A')}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


st.set_page_config(page_title="Leaf Disease Detection", layout="wide", initial_sidebar_state="collapsed")

# Styles
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #e3f2fd 0%, #f7f9fa 100%); }
    .result-card { background: rgba(255,255,255,0.95); border-radius: 18px; box-shadow: 0 4px 24px rgba(44,62,80,0.10); padding: 2.5em 2em; margin-top: 1.5em; margin-bottom: 1.5em; transition: box-shadow 0.3s; }
    .result-card:hover { box-shadow: 0 8px 32px rgba(44,62,80,0.18); }
    .disease-title { color: #1b5e20; font-size: 2.2em; font-weight: 700; margin-bottom: 0.5em; letter-spacing: 1px; text-shadow: 0 2px 8px #e0e0e0; }
    .section-title { color: #1976d2; font-size: 1.25em; margin-top: 1.2em; margin-bottom: 0.5em; font-weight: 600; letter-spacing: 0.5px; }
    .timestamp { color: #616161; font-size: 0.95em; margin-top: 1.2em; text-align: right; }
    .info-badge { display: inline-block; background: #e3f2fd; color: #1976d2; border-radius: 8px; padding: 0.3em 0.8em; font-size: 1em; margin-right: 0.5em; margin-bottom: 0.3em; }
    .symptom-list, .cause-list, .treatment-list { margin-left: 1em; margin-bottom: 0.5em; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div style='text-align: center; margin-top: 1em;'>
        <span style='font-size:2.5em;'>🌿</span>
        <h1 style='color: #1565c0; margin-bottom:0;'>Leaf Disease Detection</h1>
        <p style='color: #616161; font-size:1.15em;'>Upload a leaf image to detect diseases and get expert recommendations.</p>
    </div>
""", unsafe_allow_html=True)

api_url = "http://leaf-diseases-detect.vercel.app"

# Keep simple checkbox for Kiswahili translation (backwards compatible)
translate_output = st.checkbox("Tafsiri matokeo kwa Kiswahili", value=False)
if translate_output:
    i18n.set_locale('sw')
else:
    i18n.set_locale('en')

col1, col2 = st.columns([1, 2])
with col1:
    uploaded_file = st.file_uploader("Upload Leaf Image", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Preview")

with col2:
    if st.button(translate_text("Use sample result"), use_container_width=True):
        sample_result = {
            "disease_detected": True,
            "disease_name": "Powdery mildew",
            "disease_type": "fungal",
            "severity": "moderate",
            "confidence": 88,
            "symptoms": ["White powdery growth", "Leaf curling"],
            "possible_causes": ["High humidity", "Crowded plants"],
            "treatment": ["Increase air flow", "Remove affected leaves"],
            "chemical_recommendations": ["Sulfur", "Myclobutanil", "Trifloxystrobin"],
            "analysis_timestamp": "2026-05-23T12:31:55.979000+00:00"
        }
        render_result_card(sample_result, translate_output)

    if uploaded_file is not None:
        if st.button("🔍 Detect Disease", use_container_width=True):
            spinner_text = translate_text("Analyzing image and contacting API...")
            with st.spinner(spinner_text):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{api_url}/disease-detection-file", files=files)
                    if response.status_code == 200:
                        result = response.json()

                        if result.get("disease_type") == "invalid_image":
                            invalid_title = format_text("⚠️ Invalid Image", translate_output)
                            invalid_message = format_text("Please upload a clear image of a plant leaf for accurate disease detection.", translate_output)

                            st.markdown("<div class='result-card'>", unsafe_allow_html=True)
                            st.markdown(f"<div class='disease-title'>{invalid_title}</div>", unsafe_allow_html=True)
                            st.markdown(f"<div style='color: #ff5722; font-size: 1.1em; margin-bottom: 1em;'>{invalid_message}</div>", unsafe_allow_html=True)

                            if result.get("symptoms"):
                                st.markdown(f"<div class='section-title'>{format_text('Issue', translate_output)}</div>", unsafe_allow_html=True)
                                st.markdown("<ul class='symptom-list'>", unsafe_allow_html=True)
                                for symptom in translate_list(result.get("symptoms", [])):
                                    st.markdown(f"<li>{symptom}</li>", unsafe_allow_html=True)
                                st.markdown("</ul>", unsafe_allow_html=True)

                            if result.get("treatment"):
                                st.markdown(f"<div class='section-title'>{format_text('What to do', translate_output)}</div>", unsafe_allow_html=True)
                                st.markdown("<ul class='treatment-list'>", unsafe_allow_html=True)
                                for treat in translate_list(result.get("treatment", [])):
                                    st.markdown(f"<li>{treat}</li>", unsafe_allow_html=True)
                                st.markdown("</ul>", unsafe_allow_html=True)

                            st.markdown("</div>", unsafe_allow_html=True)

                        elif result.get("disease_detected"):
                            disease_name = result.get('disease_name', 'N/A')
                            if translate_output and isinstance(disease_name, str):
                                disease_name = translate_text(disease_name)

                            st.markdown("<div class='result-card'>", unsafe_allow_html=True)
                            st.markdown(f"<div class='disease-title'>🦠 {disease_name}</div>", unsafe_allow_html=True)
                            st.markdown(f"<span class='info-badge'>{format_text('Type', translate_output)}: {translate_text(result.get('disease_type', 'N/A')) if translate_output else result.get('disease_type', 'N/A')}</span>", unsafe_allow_html=True)
                            st.markdown(f"<span class='info-badge'>{format_text('Severity', translate_output)}: {translate_text(result.get('severity', 'N/A')) if translate_output else result.get('severity', 'N/A')}</span>", unsafe_allow_html=True)
                            st.markdown(f"<span class='info-badge'>{format_text('Confidence', translate_output)}: {result.get('confidence', 'N/A')}% </span>", unsafe_allow_html=True)

                            st.markdown(f"<div class='section-title'>{format_text('Symptoms', translate_output)}</div>", unsafe_allow_html=True)
                            st.markdown("<ul class='symptom-list'>", unsafe_allow_html=True)
                            for symptom in translate_list(result.get("symptoms", [])):
                                st.markdown(f"<li>{symptom}</li>", unsafe_allow_html=True)
                            st.markdown("</ul>", unsafe_allow_html=True)

                            st.markdown(f"<div class='section-title'>{format_text('Possible Causes', translate_output)}</div>", unsafe_allow_html=True)
                            st.markdown("<ul class='cause-list'>", unsafe_allow_html=True)
                            for cause in translate_list(result.get("possible_causes", [])):
                                st.markdown(f"<li>{cause}</li>", unsafe_allow_html=True)
                            st.markdown("</ul>", unsafe_allow_html=True)

                            st.markdown(f"<div class='section-title'>{format_text('Treatment', translate_output)}</div>", unsafe_allow_html=True)
                            st.markdown("<ul class='treatment-list'>", unsafe_allow_html=True)
                            for treat in translate_list(result.get("treatment", [])):
                                st.markdown(f"<li>{treat}</li>", unsafe_allow_html=True)
                            st.markdown("</ul>", unsafe_allow_html=True)

                            chemicals = result.get("chemical_recommendations", [])
                            if chemicals:
                                translated_chemicals = translate_list(chemicals)
                                disease_type = str(result.get('disease_type', '')).lower()
                                disease_name_check = str(result.get('disease_name', '')).lower() if result.get('disease_name') else ''
                                fungal_words = ['late blight', 'powdery mildew', 'anthracnose', 'brown spot', 'downy mildew', 'rust']
                                if 'fungal' in disease_type or any(word in disease_name_check for word in fungal_words):
                                    primary_label = format_text('Primary fungicide', translate_output)
                                else:
                                    primary_label = format_text('Primary chemical', translate_output)

                                st.markdown(f"<div class='section-title'>{format_text('Recommended Chemicals', translate_output)}</div>", unsafe_allow_html=True)
                                st.markdown(f"<div style='font-weight: 600; margin-bottom: 0.5em;'>{primary_label}: {translated_chemicals[0]}</div>", unsafe_allow_html=True)
                                if len(translated_chemicals) > 1:
                                    st.markdown(f"<div>{format_text('Also recommended', translate_output)}:</div>", unsafe_allow_html=True)
                                    st.markdown("<ul class='treatment-list'>", unsafe_allow_html=True)
                                    for chemical in translated_chemicals[1:]:
                                        st.markdown(f"<li>{chemical}</li>", unsafe_allow_html=True)
                                    st.markdown("</ul>", unsafe_allow_html=True)

                            st.markdown(f"<div class='timestamp'>🕒 {result.get('analysis_timestamp', 'N/A')}</div>", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)

                        else:
                            healthy_title = format_text("✅ Healthy Leaf", translate_output)
                            healthy_message = format_text("No disease detected in this leaf. The plant appears to be healthy!", translate_output)
                            status_label = format_text("Status", translate_output)
                            confidence_label = format_text("Confidence", translate_output)

                            st.markdown("<div class='result-card'>", unsafe_allow_html=True)
                            st.markdown(f"<div class='disease-title'>{healthy_title}</div>", unsafe_allow_html=True)
                            st.markdown(f"<div style='color: #4caf50; font-size: 1.1em; margin-bottom: 1em;'>{healthy_message}</div>", unsafe_allow_html=True)
                            st.markdown(f"<span class='info-badge'>{status_label}: {translate_text(result.get('disease_type', 'healthy')) if translate_output else result.get('disease_type', 'healthy')}</span>", unsafe_allow_html=True)
                            st.markdown(f"<span class='info-badge'>{confidence_label}: {result.get('confidence', 'N/A')}%</span>", unsafe_allow_html=True)
                            st.markdown(f"<div class='timestamp'>🕒 {result.get('analysis_timestamp', 'N/A')}</div>", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.error(f"API Error: {response.status_code}")
                        st.write(response.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
