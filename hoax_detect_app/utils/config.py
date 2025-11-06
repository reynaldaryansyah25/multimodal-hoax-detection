import streamlit as st

def apply_custom_css():
    """Apply custom CSS styling to Streamlit app"""
    st.markdown("""
    <style>
        /* Main styling */
        :root {
            --primary-color: #1E88E5;
            --success-color: #43A047;
            --danger-color: #E53935;
            --warning-color: #FB8C00;
            --bg-color: #F5F7FA;
        }
        
        /* Header styling */
        .header-container {
            background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
            padding: 40px 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(30, 136, 229, 0.2);
        }
        
        .header-container h1 {
            font-size: 2.5em;
            margin: 0;
            font-weight: 700;
        }
        
        .header-container h2 {
            font-size: 2em;
            margin: 0;
            font-weight: 700;
        }
        
        .header-container p {
            font-size: 1.1em;
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        
        /* Metric cards */
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid #1E88E5;
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }
        
        .metric-label {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .metric-value {
            font-size: 2.2em;
            font-weight: 700;
            color: #1E88E5;
            margin: 5px 0;
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 5px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(30, 136, 229, 0.2);
        }
        
        .stButton > button:hover {
            box-shadow: 0 4px 12px rgba(30, 136, 229, 0.4);
            transform: translateY(-2px);
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 10px 20px;
            background: transparent;
            border-bottom: 2px solid #E0E0E0;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            border-bottom: 2px solid #1E88E5;
            color: #1E88E5;
        }
        
        /* Text input styling */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            border: 1px solid #E0E0E0 !important;
            border-radius: 5px !important;
        }
        
        /* Success/Warning/Info styling */
        .stSuccess {
            background-color: #E8F5E9 !important;
            border: 1px solid #43A047 !important;
            border-radius: 5px !important;
        }
        
        .stWarning {
            background-color: #FFF3E0 !important;
            border: 1px solid #FB8C00 !important;
            border-radius: 5px !important;
        }
        
        .stInfo {
            background-color: #E3F2FD !important;
            border: 1px solid #1E88E5 !important;
            border-radius: 5px !important;
        }
    </style>
    """, unsafe_allow_html=True)

# Configuration constants
CONFIG = {
    "app_name": "HoaxDetect",
    "version": "1.0.0",
    "author": "Reynald Aryansyah",
    "max_file_size": 100 * 1024 * 1024,  # 100 MB
    "supported_image_formats": ["jpg", "jpeg", "png"],
    "supported_audio_formats": ["mp3", "wav", "ogg", "m4a"],
    "supported_video_formats": ["mp4", "mov", "avi"],
}
