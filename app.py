import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
from fpdf import FPDF
import datetime
import time
import cloudinary
import cloudinary.uploader
import cloudinary.api

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Katy & Wilvidez - Wedding Album", page_icon="💍", layout="wide")

# Directorios
GALLERY_DIR = "galeria"
ASSETS_DIR = "assets"
FRAME_PATH = os.path.join(ASSETS_DIR, "marco.png")

# Asegurar que los directorios existan al iniciar (Evita FileNotFoundError en la nube)
if not os.path.exists(GALLERY_DIR):
    os.makedirs(GALLERY_DIR)
if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

# --- CONFIGURACIÓN DE CLOUDINARY (Cloud Storage) ---
# Usamos secretos de Streamlit para la nube, y las llaves proporcionadas para local
try:
    if "CLOUDINARY_CLOUD_NAME" in st.secrets:
        cloudinary.config(
            cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
            api_key = st.secrets["CLOUDINARY_API_KEY"],
            api_secret = st.secrets["CLOUDINARY_API_SECRET"],
            secure = True
        )
    else:
        # Fallback con las credenciales proporcionadas por el usuario
        cloudinary.config(
            cloud_name = "dfbctfdsw",
            api_key = "262358627828791",
            api_secret = "oiVl4DAJSq_5NJ5P-8MrdwdUDnE",
            secure = True
        )
except:
    # Si falla st.secrets (local sin secrets.toml), usar credenciales directas
    cloudinary.config(
        cloud_name = "dfbctfdsw",
        api_key = "262358627828791",
        api_secret = "oiVl4DAJSq_5NJ5P-8MrdwdUDnE",
        secure = True
    )

# --- INICIALIZACIÓN DE ESTADO SEGURO ---
# admin_view: 'panel' o 'viewer'
for key in ['last_result_path', 'last_pdf_path', 'show_celebration', 'creation_time', 'is_logged_in', 'admin_view']:
    if key not in st.session_state:
        if key in ['show_celebration', 'is_logged_in']:
            st.session_state[key] = False
        elif key == 'admin_view':
            st.session_state[key] = 'panel'
        else:
            st.session_state[key] = None

if 'file_uploader_key' not in st.session_state:
    st.session_state.file_uploader_key = 0

# Limpieza de llaves obsoletas para evitar errores de Streamlit
if 'file_input' in st.session_state:
    del st.session_state['file_input']

import base64

def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Imagen de fondo específica del usuario
BG_IMAGE_PATH = os.path.join(ASSETS_DIR, "background_wedding.jpg")
if os.path.exists(BG_IMAGE_PATH):
    bin_str = get_base64(BG_IMAGE_PATH)
    page_bg_img = f'''
    <style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{bin_str}");
        background-size: cover;
        background-attachment: fixed;
    }}
    .stApp::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(250, 245, 237, 0.998); /* 99.8% Sólido: rastro microscópico de la imagen de fondo */
        z-index: -1;
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

def sync_from_cloudinary():
    """Descarga todas las fotos de Cloudinary a la carpeta local galeria"""
    try:
        if not os.path.exists(GALLERY_DIR):
            os.makedirs(GALLERY_DIR)
            
        # Listar archivos en la carpeta de la boda
        resources = cloudinary.api.resources(
            type = "upload",
            prefix = "recuerdos_boda/",
            max_results = 500
        )
        
        count = 0
        import requests
        for res in resources.get('resources', []):
            url = res.get('secure_url')
            public_id = res.get('public_id')
            # Extraer el nombre del archivo de la ruta (editorial_...)
            filename = public_id.split('/')[-1] + ".png"
            local_path = os.path.join(GALLERY_DIR, filename)
            
            if not os.path.exists(local_path):
                img_data = requests.get(url).content
                with open(local_path, 'wb') as handler:
                    handler.write(img_data)
                count += 1
        return count
    except Exception as e:
        st.error(f"Error al sincronizar: {e}")
        return 0

def delete_memory(filename):
    """Borra un recuerdo localmente y en Cloudinary"""
    try:
        # 1. Borrado Local
        local_path = os.path.join(GALLERY_DIR, filename)
        if os.path.exists(local_path):
            os.remove(local_path)
            
        # 2. Borrado en Cloudinary
        # El public_id en mi config es recuerdos_boda/nombre_sin_extension
        public_id = f"recuerdos_boda/{filename.replace('.png', '')}"
        cloudinary.uploader.destroy(public_id)
        return True
    except Exception as e:
        st.error(f"Error al borrar: {e}")
        return False

# --- ESTILOS PREMIUM (Diseño Editorial y Responsivo) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Cormorant+Garamond:ital,wght@0,300;0,600;1,400&display=swap');
    
    /* Configuración Base */
    .stApp {
        font-family: 'Cormorant Garamond', serif;
    }
    
    .main-container {
        padding: 40px 20px;
        max-width: 800px;
        margin: auto;
    }

    /* Ajustes para Móvil */
    @media (max-width: 768px) {
        .main-container {
            padding: 20px 10px;
        }
        h1 { font-size: 2.5rem !important; }
        h2 { font-size: 1.8rem !important; }
    }

    /* Resalte Máximo de Texto (Halo Oro Suave Luxury) */
    h1, h2, h3, p, label, .stMarkdown, .stSubheader {
        color: #1a140f !important; /* Negro café profundo luxury */
        text-align: center;
        font-weight: 700 !important;
        /* Efecto de borde beige seda extra-nítido */
        text-shadow: 
            -1.5px -1.5px 0 #ede0c8,  
             1.5px -1.5px 0 #ede0c8,
            -1.5px  1.5px 0 #ede0c8,
             1.5px  1.5px 0 #ede0c8,
            -2px -2px 0 #ede0c8,  
             2px -2px 0 #ede0c8,
            -2px  2px 0 #ede0c8,
             2px  2px 0 #ede0c8,
             0px 3px 6px rgba(0,0,0,0.2) !important;
    }
    
    h1 {
        font-family: 'Playfair Display', serif;
        font-size: 4.8rem;
        font-weight: 900 !important;
        color: #2a1f14 !important;
        margin-bottom: -15px;
        letter-spacing: -1px;
    }
    
    .stSubheader {
        font-family: 'Cormorant Garamond', serif !important;
        font-style: italic;
        font-size: 1.8rem !important;
        color: #8a6d3b !important;
        margin-top: 20px !important;
    }

    /* Inputs Luxury */
    .stTextInput input, .stTextArea textarea {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 1.5px solid #c9a96e !important;
        border-radius: 0 !important;
        color: #1a140f !important;
        font-size: 1.3rem !important;
        padding-bottom: 5px !important;
    }

    /* Botón Premium */
    .stButton button {
        background: linear-gradient(135deg, #c9a96e 0%, #8a6d3b 100%) !important;
        color: white !important;
        border: none !important;
        padding: 15px 30px !important;
        border-radius: 50px !important;
        font-weight: 600 !important;
        letter-spacing: 1px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(201, 169, 110, 0.3) !important;
        display: block !important;
        margin: 20px auto !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(201, 169, 110, 0.5) !important;
    }

    /* Cargador de Archivos */
    section[data-testid="stFileUploadDropzone"] {
        background: white !important;
        border: 2px dashed #c9a96e !important;
        border-radius: 12px !important;
        padding: 20px !important;
    }

    /* Preview de Imagen */
    .stImage img {
        border: 4px solid white !important;
        border-radius: 4px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15) !important;
        max-width: 100% !important;
        height: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

def reset_form():
    # Limpiar todas las variables de estado relacionadas con el recuerdo actual
    st.session_state.last_result_path = None
    st.session_state.last_pdf_path = None
    st.session_state.show_celebration = False
    st.session_state.creation_time = None
    # Limpiar los widgets usando sus llaves (keys)
    if 'guest_input' in st.session_state: st.session_state.guest_input = ""
    if 'msg_input' in st.session_state: st.session_state.msg_input = ""
    # Para el file_uploader, rotamos la llave para forzar el reset
    st.session_state.file_uploader_key += 1

def celebrate_wedding():
    # Solo renderizar si el estado de celebración está activo
    if st.session_state.get('show_celebration', False):
        # Usar un contenedor vacío para mayor estabilidad en el DOM de Streamlit
        placeholder = st.empty()
        
        # Gran Lluvia de Pétalos Majesty (Alta Densidad y Realismo)
        html_elements = ""
        for i in range(150): 
            if i % 2 == 0:
                color = "linear-gradient(145deg, #cc0000, #7a0000)" 
            else:
                color = "linear-gradient(145deg, #ffffff, #e8e8e8)" 
                
            left = (i * 0.67) % 100 
            delay = i * 0.03 
            dur = 2.5 + (i % 4) 
            size_w = 18 + (i % 25) 
            size_h = 25 + (i % 30)
            rot = i * 27
            
            html_elements += f'<div class="petal" style="left:{left}%; animation-delay:{delay}s; animation-duration:{dur}s; width:{size_w}px; height:{size_h}px; background:{color}; transform: rotate({rot}deg);"></div>'
        
        placeholder.markdown(f"""
            <div class="rain-container" id="wedding-rain">
                {html_elements}
            </div>
            <style>
            .rain-container {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                pointer-events: none;
                z-index: 100000;
                overflow: hidden;
            }}
            .petal {{
                position: absolute;
                top: -100px;
                border-radius: 20px 150px 20px 150px;
                animation: petal-fall ease-in-out forwards;
                box-shadow: 2px 4px 12px rgba(0,0,0,0.15);
                opacity: 0.95;
            }}
            @keyframes petal-fall {{
                0% {{ transform: translateY(0) rotate(0deg) scale(0.7); opacity: 0; }}
                10% {{ opacity: 1; }}
                95% {{ opacity: 1; }}
                100% {{ transform: translateY(115vh) rotate(1440deg) translateX(200px) scale(1.1); opacity: 0; }}
            }}
            </style>
        """, unsafe_allow_html=True)
        # Desactivar estado tras renderizar
        st.session_state.show_celebration = False

def process_image(uploaded_files, message, guest_name=""):
    try:
        # --- 1. CONFIGURACIÓN Y LIENZO ---
        canvas_width, canvas_height = 1080, 1920
        cream_bg = (250, 245, 237) # #faf5ed
        gold_color = (180, 150, 90) # Oro viejo más elegante
        dark_text = (20, 15, 10) # Casi negro editorial
        accent_text = (120, 90, 60) # Bronce elegante
        
        canvas = Image.new("RGB", (canvas_width, canvas_height), cream_bg)
        
        # --- 2. FILIGRANA DE FONDO (MARCA DE AGUA) ---
        bg_path = os.path.join(ASSETS_DIR, "background_wedding.jpg")
        if os.path.exists(bg_path):
            try:
                bg_img = Image.open(bg_path).convert("RGBA")
                bg_img = ImageOps.fit(bg_img, (canvas_width, canvas_height), Image.LANCZOS)
                # Crear máscara de opacidad absoluta infinitesimal (aprox 0.4%)
                alpha = bg_img.getchannel('A')
                new_alpha = alpha.point(lambda i: 1 if i > 0 else 0) # El mínimo posible antes de desaparecer
                bg_img.putalpha(new_alpha)
                # Pegar sobre el lienzo crema
                canvas.paste(bg_img, (0,0), bg_img)
            except: pass

        draw = ImageDraw.Draw(canvas)
        
        # --- 3. BORDES Y ORNAMENTOS ---
        margin = 15
        draw.rectangle([margin, margin, canvas_width-margin, canvas_height-margin], outline=gold_color, width=4)
        draw.rectangle([margin+12, margin+12, canvas_width-margin-12, canvas_height-margin-12], outline=gold_color, width=1)
        
        # Esquinas ornamentadas
        for x_e, y_e in [(margin, margin), (canvas_width-margin, margin), (margin, canvas_height-margin), (canvas_width-margin, canvas_height-margin)]:
            draw.ellipse([x_e-12, y_e-12, x_e+12, y_e+12], fill=gold_color)

        # --- SELLO/LOGO CIRCULAR PREMIUM ---
        if os.path.exists(bg_path):
            try:
                logo_size = 160
                logo_img = Image.open(bg_path).convert("RGBA")
                logo_img = ImageOps.fit(logo_img, (logo_size, logo_size), Image.LANCZOS)
                
                # Máscara circular
                mask = Image.new('L', (logo_size, logo_size), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, logo_size, logo_size), fill=255)
                
                # Aplicar máscara y borde dorado
                logo_circular = Image.new('RGBA', (logo_size, logo_size), (0,0,0,0))
                logo_circular.paste(logo_img, (0,0), mask)
                
                # Posición del logo (Arriba en el centro)
                logo_x = (canvas_width - logo_size) // 2
                logo_y = 70
                canvas.paste(logo_circular, (logo_x, logo_y), logo_circular)
                
                # Anillo dorado alrededor del logo
                draw.ellipse([logo_x-2, logo_y-2, logo_x+logo_size+2, logo_y+logo_size+2], outline=gold_color, width=3)
            except: pass
            
        # --- 4. ENCABEZADO Y TIPOGRAFÍA ---
        def get_font(size, bold=False, cursive=False):
            # Fuentes de boda de alta gama
            font_candidates = []
            if cursive:
                # Nombres de archivos de fuentes de lujo
                font_candidates += ["ITCEDSCR.TTF", "script.ttf", "Edwardian Script ITC.ttf", "PLSCRT.TTF", "vladimir.ttf", "mtcorsva.ttf"]
            if bold:
                font_candidates += ["georgiab.ttf", "timesbd.ttf", "DejaVuSerif-Bold.ttf", "LiberationSerif-Bold.ttf"]
            
            font_candidates += ["georgia.ttf", "times.ttf", "DejaVuSerif.ttf", "LiberationSerif-Regular.ttf", "arial.ttf"]
            
            for f_name in font_candidates:
                # 1. Probar en la carpeta assets (RECOMENDADO PARA LA NUBE)
                asset_path = os.path.join(ASSETS_DIR, f_name)
                # 2. Probar por nombre directo (Windows system fonts)
                # 3. Probar en rutas comunes de Linux (Nube)
                linux_paths = ["/usr/share/fonts/truetype/dejavu/", "/usr/share/fonts/truetype/liberation/"]
                
                search_targets = [asset_path, f_name]
                for lp in linux_paths:
                    search_targets.append(os.path.join(lp, f_name))
                
                for target in search_targets:
                    try:
                        return ImageFont.truetype(target, size)
                    except:
                        continue
            
            # Si nada funciona, al menos que no sea diminuto
            try:
                # Intentar cargar la fuente default de Linux que sí acepta tamaño en versiones nuevas
                return ImageFont.truetype("DejaVuSerif.ttf", size)
            except:
                return ImageFont.load_default()

        # Helper para dibujar texto con resalte (aura oro suave más fuerte)
        def draw_text_with_halo(pos, text, font, fill, anchor="mm"):
            # Aura beige seda nítida
            halo_color = (237, 224, 200, 255) # Máxima opacidad
            # Múltiples offsets para un borde más robusto
            offsets = [(1,1), (-1,-1), (1,-1), (-1,1), (2,2), (-2,-2), (2,-2), (-2,2)]
            for offset in offsets:
                draw.text((pos[0]+offset[0], pos[1]+offset[1]), text, font=font, fill=halo_color, anchor=anchor)
            draw.text(pos, text, font=font, fill=fill, anchor=anchor)

        # Título Label
        label_font = get_font(30, bold=True)
        draw_text_with_halo((canvas_width//2, 260), "ÁLBUM DE RECUERDOS", label_font, gold_color)
        
        # 1. Título "Nuestra Boda"
        names_font_main = get_font(120, cursive=True)
        draw_text_with_halo((canvas_width//2, 330), "Nuestra Boda", names_font_main, dark_text)
        
        # 2. Subtítulo de los Novios (Ajuste dinámico)
        names_text = "Katy Jimenez & Wilvidez Toro"
        base_size = 85
        names_font_sub = get_font(base_size, cursive=True)
        
        while draw.textbbox((0, 0), names_text, font=names_font_sub)[2] > (canvas_width - 150):
            base_size -= 5
            names_font_sub = get_font(base_size, cursive=True)
            if base_size < 30: break
            
        draw_text_with_halo((canvas_width//2, 400), names_text, names_font_sub, accent_text)
        
        # Divisor
        line_y = 445
        draw.line([300, line_y, 780, line_y], fill=gold_color, width=2)
        draw.regular_polygon((canvas_width//2, line_y, 12), 4, fill=gold_color)

        # Fecha Fija de la Boda
        date_text = "24 · ABRIL · 2026"
        draw_text_with_halo((canvas_width//2, 490), date_text, label_font, accent_text)

        # --- 5. COLLAGE DE FOTOS (1+2 Layout) ---
        num_fotos = len(uploaded_files)
        main_y, main_h = 530, 650
        sec_y, sec_h = 1200, 380
        photo_margin = 100
        
        # Foto 1
        if num_fotos >= 1:
            try:
                uploaded_files[0].seek(0)
                img1 = ImageOps.fit(Image.open(uploaded_files[0]).convert("RGB"), (canvas_width - photo_margin*2, main_h), Image.LANCZOS)
                canvas.paste(img1, (photo_margin, main_y))
                draw.rectangle([photo_margin, main_y, canvas_width-photo_margin, main_y+main_h], outline=gold_color, width=6)
            except: pass

        # Fotos 2 y 3
        if num_fotos >= 2:
            img_w = (canvas_width - photo_margin*2 - 40) // 2
            for i in range(1, min(num_fotos, 3)):
                try:
                    uploaded_files[i].seek(0)
                    img = ImageOps.fit(Image.open(uploaded_files[i]).convert("RGB"), (img_w, sec_h), Image.LANCZOS)
                    x_pos = photo_margin + (i-1) * (img_w + 40)
                    canvas.paste(img, (x_pos, sec_y))
                    draw.rectangle([x_pos, sec_y, x_pos+img_w, sec_y+sec_h], outline=gold_color, width=5)
                except: pass

        # --- 6. MENSAJE Y PIE ---
        # Capitalizar mensaje y firma: primera letra siempre en mayúscula
        if message:
            message = message.strip()
            message = message[0].upper() + message[1:] if message else ""
        if guest_name:
            guest_name = guest_name.strip()
            guest_name = guest_name[0].upper() + guest_name[1:] if guest_name else ""
            
        msg_y_base = sec_y + sec_h + 60
        # Reducimos un poco más para máxima elegancia y seguridad
        m_font = get_font(38, cursive=True) 
        
        wrapped_lines = []
        words = message.split()
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            bbox = draw.textbbox((0, 0), test_line, font=m_font)
            if (bbox[2] - bbox[0]) < 850: current_line = test_line
            else:
                wrapped_lines.append(current_line.strip())
                current_line = word + " "
        wrapped_lines.append(current_line.strip())

        for i, l_text in enumerate(wrapped_lines[:5]):
            line_y = msg_y_base + (i * 45)
            draw_text_with_halo((canvas_width//2, line_y), l_text, m_font, dark_text)

        # --- FIRMA DEL INVITADO ---
        if guest_name:
            sig_font = get_font(32, cursive=True)
            sig_y = msg_y_base + (len(wrapped_lines[:5]) * 45) + 35
            draw_text_with_halo((canvas_width//2, sig_y), f"— {guest_name.strip()} —", sig_font, accent_text)

        # Pie de página (Subimos para evitar cortes en el borde de 1920)
        footer_y = 1830 
        footer_font = get_font(35, cursive=True)
        draw.line([380, footer_y, 700, footer_y], fill=gold_color, width=1)
        draw_text_with_halo((canvas_width//2, footer_y + 40), "Para siempre & por siempre", footer_font, accent_text)

        # --- 7. GUARDAR ---
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        final_path = os.path.join(GALLERY_DIR, f"editorial_{timestamp}.png")
        canvas.save(final_path, "PNG")
        
        # --- 8. SUBIR A LA NUBE (CLOUDINARY) ---
        try:
            with st.spinner("Sincronizando con la nube..."):
                upload_result = cloudinary.uploader.upload(
                    final_path,
                    public_id = f"boda/editorial_{timestamp}",
                    folder = "recuerdos_boda"
                )
        except Exception as cloud_err:
            st.warning(f"Guardado local exitoso, pero hubo un detalle con la nube: {cloud_err}")
            
        return final_path
    except Exception as e:
        st.error(f"Error en el refinamiento: {e}")
        return None

def generate_pdf(single_image=None):
    try:
        pdf = FPDF()
        if single_image:
            images = [os.path.abspath(single_image)]
        else:
            # Buscar tanto recuerdos viejos como los nuevos "editorial_" usando rutas absolutas
            images = [os.path.abspath(os.path.join(GALLERY_DIR, f)) for f in os.listdir(GALLERY_DIR) 
                     if f.startswith('recuerdo_') or f.startswith('editorial_')]
            # Ordenar por fecha de modificación (los más nuevos primero)
            images.sort(key=os.path.getmtime, reverse=True)
            
        if not images:
            return None
            
        for img_path in images:
            if os.path.exists(img_path):
                pdf.add_page()
                # Fondo Editorial Luxury (Crema suave)
                pdf.set_fill_color(250, 245, 237)
                pdf.rect(0, 0, 210, 297, 'F')
                
                # Marco de página ornamental (Dorado muy fino cerca del borde del papel)
                pdf.set_draw_color(180, 150, 90) # gold_color
                pdf.set_line_width(0.5)
                pdf.rect(5, 5, 200, 287) # Margen de 5mm en todo el papel
                
                # Maximización del Recuerdo (Aprovechando el 100% de la altura A4)
                # Proporción 9:16 -> En 297mm de alto el ancho es 167.06mm
                img_w = 167.06
                img_h = 297
                pdf.image(img_path, x=(210-img_w)/2, y=0, w=img_w, h=img_h)
            
        out_name = "tu_recuerdo.pdf" if single_image else "album_boda.pdf"
        pdf.output(out_name)
        return out_name, len(images)
    except Exception as e:
        st.error(f"Error PDF: {e}")
        return None, 0

# Función eliminada: show_pdf_preview (reemplazada por visor digital nativo)

# --- INTERFAZ STREAMLIT ---

# --- INTERFAZ STREAMLIT ---

menu = ["✨ Crear Recuerdo", "🔐 Panel Admin"]
choice = st.sidebar.selectbox("Explorar:", menu)

if choice == "✨ Crear Recuerdo":
    st.markdown('<h1 class="wedding-title" style="margin-bottom: -20px;">Nuestra Boda</h1>', unsafe_allow_html=True)
    st.markdown('<h2 class="novios-title" style="font-family: \'Edwardian Script ITC\', \'Palace Script MT\', cursive; font-size: 3.5rem; color: #8a6d3b; text-align: center; margin-bottom: 20px;">Katy Jimenez & Wilvidez Toro</h2>', unsafe_allow_html=True)
    
    # Ejecutar celebración si está activa en el estado
    celebrate_wedding()
    st.markdown('<p class="wedding-subtitle">¡Captura y comparte la magia de este día único!</p>', unsafe_allow_html=True)
    # --- LÓGICA DE LIMPIEZA AUTOMÁTICA (40 SEGUNDOS) ---
    if st.session_state.get('creation_time'):
        elapsed = time.time() - st.session_state.creation_time
        if elapsed > 40:
            reset_form()
            st.rerun()
            
    st.subheader("📸 Comparte tu Alegría")
    st.write("Tu presencia hace este día aún más especial. Sube hasta 3 de tus momentos favoritos y deja un mensaje con todo tu amor.")
    
    with st.container():
        # Usamos una llave dinámica para poder resetearlo
        uploader_key = f"file_input_{st.session_state.file_uploader_key}"
        uploaded_files = st.file_uploader("Selecciona tus fotos más felices (máximo 3)", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key=uploader_key)
        col1, col2 = st.columns([1, 1])
        with col1:
            guest_name = st.text_input("Tu Nombre o Familia", placeholder="Ejem: Juan y María / Familia Pérez", key="guest_input")
        with col2:
            message = st.text_input("Tu Dedicatoria", max_chars=100, placeholder="Ejem: ¡Felicidades hoy y siempre!", key="msg_input")
        
        if st.button("💝 Crear y Guardar mi Recuerdo"):
            if uploaded_files and message:
                if len(uploaded_files) > 3:
                    st.warning("Solo se procesarán las primeras 3 fotos. ¡Elige las mejores! ✨")
                
                with st.spinner("Estamos preparando tu recuerdo con mucho cariño..."):
                    result_path = process_image(uploaded_files, message, guest_name)
                    if result_path:
                        # Generar PDF individual
                        pdf_path, _ = generate_pdf(single_image=result_path)
                        
                        # Guardar en estado para persistencia tras el rerun
                        st.session_state.last_result_path = result_path
                        st.session_state.last_pdf_path = pdf_path
                        st.session_state.show_celebration = True
                        st.session_state.creation_time = time.time() # Registrar momento de creación
                        st.rerun()
            else:
                st.warning("Por favor, sube al menos una foto y escribe un mensaje para que podamos atesorarlo.")

        # --- MOSTRAR RESULTADOS PERSISTENTES ---
        if st.session_state.get('last_result_path'):
            st.success("¡Gracias por compartir este momento con nosotros! 🎉")
            
            res_path = st.session_state.last_result_path
            pdf_p = st.session_state.get('last_pdf_path')
            
            if pdf_p and os.path.exists(pdf_p):
                with open(pdf_p, "rb") as f:
                    st.download_button(
                        label="💖 Descargar mi Recuerdo en PDF",
                        data=f,
                        file_name="mi_recuerdo_boda.pdf",
                        mime="application/pdf",
                        on_click=reset_form # Limpiar al descargar
                    )
            
            if os.path.exists(res_path):
                st.image(res_path, caption="Así luce tu dedicatoria ✨", use_container_width=True)
            
            # Mostrar temporizador visual sutil con guarda de seguridad
            if st.session_state.get('creation_time'):
                remaining = int(40 - (time.time() - st.session_state.creation_time))
                if remaining > 0:
                    st.caption(f"La pantalla se limpiará automáticamente en {remaining} segundos.")

    st.markdown('<div class="footer">"El amor no consiste en mirarse el uno al otro, sino en mirar juntos en la misma dirección."</div>', unsafe_allow_html=True)

else:
    if not st.session_state.is_logged_in:
        st.subheader("🔐 Acceso al Tesoro de Recuerdos")
        password = st.text_input("Contraseña de Administrador", type="password")
        if st.button("🗝️ Ingresar al Sistema"):
            if password == "admin123":
                st.session_state.is_logged_in = True
                st.rerun()
            else:
                st.error("Lo sentimos, esa no es la llave correcta. Inténtalo de nuevo. ✨")
    else:
        if st.session_state.admin_view == 'panel':
            # Título de bienvenida del Administrador
            st.markdown('<h1 class="wedding-title" style="font-size: 2.8rem; border-bottom: 2px solid #c9a96e; padding-bottom: 10px;">Panel de Administrador</h1>', unsafe_allow_html=True)
            st.markdown('<h2 class="novios-title" style="font-family: \'Edwardian Script ITC\', \'Palace Script MT\', cursive; font-size: 3rem; color: #8a6d3b; text-align: center; margin-top: 10px;">Katy Jimenez & Wilvidez Toro</h2>', unsafe_allow_html=True)
            
            st.success("¡Bienvenido al sistema central de recuerdos! ✨")
            
            if st.sidebar.button("🚪 Cerrar Sesión"):
                st.session_state.is_logged_in = False
                st.session_state.admin_pdf_ready = None
                st.session_state.admin_view = 'panel'
                st.rerun()

            st.write("### 📖 Gestión del Álbum Digital")
            st.info("Desde aquí puedes compilar el libro de recuerdos y visualizarlo antes de la descarga final.")
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("🔄 Sincronizar Nube"):
                    with st.spinner("Trayendo todos los recuerdos de la nube..."):
                        synced = sync_from_cloudinary()
                        st.success(f"¡Sincronización terminada! {synced} fotos nuevas descargadas.")
            
            with col_b:
                if st.button("✨ Actualizar Datos"):
                    with st.spinner("Compilando todos los deseos y sonrisas..."):
                        pdf_file, count = generate_pdf()
                        if pdf_file:
                            st.session_state.admin_pdf_ready = pdf_file
                            st.session_state.admin_pdf_count = count
                            st.success(f"¡Álbum compilado! {count} recuerdos detectados.")
            
            if st.session_state.get('admin_pdf_ready'):
                with col_c:
                    if st.button("📖 ABRIR VISOR"):
                        st.session_state.admin_view = 'viewer'
                        st.rerun()
                
                # Fila de descarga
                pdf_file = st.session_state.admin_pdf_ready
                if os.path.exists(pdf_file):
                    with open(pdf_file, "rb") as f:
                        st.download_button(
                            label="📥 DESCARGAR LIBRO COMPLETO (PDF)",
                            data=f,
                            file_name="Libro_de_Recuerdos_Boda.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
            
            st.write("---")
            st.write("### 📸 Galería y Control de Contenido")
            
            # Asegurar que el directorio existe antes de listar
            if not os.path.exists(GALLERY_DIR):
                os.makedirs(GALLERY_DIR)
                
            files = [f for f in os.listdir(GALLERY_DIR) if f.startswith('editorial_') or f.startswith('recuerdo_')]
            files.sort(key=lambda x: os.path.getmtime(os.path.join(GALLERY_DIR, x)), reverse=True)
            
            if len(files) > 0:
                st.info(f"Mostrando {len(files)} recuerdos. Puedes eliminarlos si son pruebas.")
                
                # Usar tabs o expansores para no saturar la vista móvil
                with st.expander("🗑️ PANEL DE BORRADO DE PRUEBAS"):
                    # Crear filas para borrado
                    for f in files:
                        col_img, col_btn = st.columns([3, 1])
                        with col_img:
                            st.write(f"📄 {f}")
                        with col_btn:
                            if st.button("Borrar", key=f"del_{f}"):
                                if delete_memory(f):
                                    st.success(f"¡{f} eliminado!")
                                    st.rerun()
                
                st.write("#### Vista Previa Rápida")
                cols = st.columns(4)
                for idx, file in enumerate(files):
                    img_path = os.path.join(GALLERY_DIR, file)
                    cols[idx % 4].image(img_path, use_container_width=True)
            else:
                st.warning("El álbum aún está esperando su primera sonrisa.")

        elif st.session_state.admin_view == 'viewer':
            # MODO VISOR DIGITAL (Pantalla Completa)
            st.markdown('<h1 class="wedding-title" style="font-size: 2.2rem; text-align: center;">📖 Visor de Álbum Digital</h1>', unsafe_allow_html=True)
            
            if st.button("⬅️ Volver al Panel de Control"):
                st.session_state.admin_view = 'panel'
                st.rerun()
            
            st.write("---")
            
            # Obtener todas las imágenes en orden
            images = [os.path.join(GALLERY_DIR, f) for f in os.listdir(GALLERY_DIR) 
                     if f.startswith('recuerdo_') or f.startswith('editorial_')]
            images.sort(key=os.path.getmtime, reverse=True)
            
            if not images:
                st.warning("No hay páginas que mostrar en el álbum todavía.")
            else:
                st.info(f"Visualizando {len(images)} páginas del libro de recuerdos.")
                
                # Contenedor centrado para el álbum
                for i, img_path in enumerate(images):
                    st.markdown(f'<p style="text-align:center; color:#8a6d3b; font-weight:bold; margin-top:30px;">— Página {i+1} —</p>', unsafe_allow_html=True)
                    
                    # Usamos HTML para asegurar que la imagen sea responsiva y elegante
                    with open(img_path, "rb") as f:
                        data = base64.b64encode(f.read()).decode("utf-8")
                    
                    st.markdown(f"""
                        <div style="display: flex; justify-content: center; padding: 10px;">
                            <img src="data:image/png;base64,{data}" class="album-page">
                        </div>
                    """, unsafe_allow_html=True)
                    
                st.write("---")
                if st.button("🔝 Volver al Inicio del Álbum"):
                    st.rerun()

