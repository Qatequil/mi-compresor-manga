import streamlit as st
import fitz  # PyMuPDF
import img2pdf
from PIL import Image, ImageEnhance, ImageStat
import io
import zipfile

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Manga PDF Toolbox", page_icon="📚", layout="wide")

# --- FUNCIONES LÓGICAS (EL CEREBRO) ---

def es_blanco_y_negro(img):
    if img.mode in ("L", "1"): return True
    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
    hsv_img = img.convert('HSV')
    banda_saturacion = hsv_img.split()[1]
    max_sat = ImageStat.Stat(banda_saturacion).extrema[0][1]
    return max_sat < 15

# --- INTERFAZ LATERAL (MENÚ) ---
st.sidebar.title("🎮 Panel de Control")
opcion = st.sidebar.radio(
    "Selecciona una herramienta:",
    ["🏠 Inicio", "⚡ Compresor Inteligente", "✂️ Recortador de Páginas", "📁 Imágenes a PDF (ZIP)"]
)

# --- 🏠 PÁGINA DE INICIO ---
if opcion == "🏠 Inicio":
    st.title("Manga PDF Ultimate Toolbox 📚")
    st.write("Bienvenido a tu suite de herramientas para Manga y Novelas.")
    st.info("Selecciona una herramienta en el menú de la izquierda para comenzar.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### ✨ Funciones Disponibles:
        - **Compresor:** Reduce el peso detectando color automáticamente.
        - **Recortador:** Borra páginas específicas de un PDF.
        - **Pixelador:** Convierte imágenes a Pixel Art para Blue Marble.
        - **Imágenes a PDF:** Convierte un archivo ZIP con fotos en un PDF.
        """)
    with col2:
        st.image("https://images.unsplash.com/photo-1578632738980-30fc71985473?auto=format&fit=crop&q=80&w=400", caption="Optimiza tu lectura")

# --- ⚡ COMPRESOR INTELIGENTE ---
elif opcion == "⚡ Compresor Inteligente":
    st.title("Compresor Inteligente Híbrido 🧠")
    archivo = st.file_uploader("Sube tu PDF pesado", type=["pdf"])
    
    if archivo:
        if st.button("🚀 Iniciar Compresión"):
            barra = st.progress(0)
            doc = fitz.open(stream=archivo.read(), filetype="pdf")
            imgs_opt = []
            for i in range(len(doc)):
                pagina = doc[i]
                lista_img = pagina.get_images(full=True)
                if lista_img:
                    xref = lista_img[0][0]
                    img_data = doc.extract_image(xref)["image"]
                    with Image.open(io.BytesIO(img_data)) as img:
                        # Redimensión
                        if img.height > 1600:
                            img = img.resize((int(img.width * (1600/img.height)), 1600), Image.Resampling.LANCZOS)
                        
                        buf = io.BytesIO()
                        if es_blanco_y_negro(img):
                            img = img.convert("L")
                            img = ImageEnhance.Contrast(img).enhance(1.4)
                            img.save(buf, format="JPEG", quality=70, optimize=True)
                        else:
                            if img.mode != "RGB": img = img.convert("RGB")
                            img.save(buf, format="JPEG", quality=80, optimize=True)
                        imgs_opt.append(buf.getvalue())
                barra.progress((i + 1) / len(doc))
            
            pdf_final = img2pdf.convert(imgs_opt)
            st.download_button("⬇️ Descargar PDF Optimizado", pdf_final, f"mini_{archivo.name}", "application/pdf")

# --- ✂️ RECORTADOR DE PÁGINAS ---
elif opcion == "✂️ Recortador de Páginas":
    st.title("Recortador de PDFs ✂️")
    archivo = st.file_uploader("Sube el PDF a editar", type=["pdf"])
    paginas_input = st.text_input("Páginas a BORRAR (separadas por comas, ej: 1, 3, 5)")
    
    if archivo and paginas_input:
        if st.button("Eliminar Páginas"):
            doc = fitz.open(stream=archivo.read(), filetype="pdf")
            indices_a_borrar = [int(x.strip()) - 1 for x in paginas_input.split(",")]
            
            # Borrar de atrás hacia adelante para no arruinar los índices
            for indice in sorted(indices_a_borrar, reverse=True):
                if 0 <= indice < len(doc):
                    doc.delete_page(indice)
            
            buf = io.BytesIO()
            doc.save(buf)
            st.download_button("⬇️ Descargar PDF Recortado", buf.getvalue(), f"editado_{archivo.name}", "application/pdf")

# --- 📁 IMÁGENES A PDF (ZIP) ---
elif opcion == "📁 Imágenes a PDF (ZIP)":
    st.title("Creador de PDF desde Imágenes 📁")
    st.write("Sube un archivo ZIP que contenga tus imágenes (JPG/PNG).")
    archivo_zip = st.file_uploader("Sube el archivo ZIP", type=["zip"])
    
    if archivo_zip:
        if st.button("Convertir a PDF"):
            with zipfile.ZipFile(archivo_zip, "r") as z:
                nombres = sorted([n for n in z.namelist() if n.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
                imgs_data = []
                for nombre in nombres:
                    imgs_data.append(z.read(nombre))
                
            if imgs_data:
                pdf_bytes = img2pdf.convert(imgs_data)
                st.download_button("⬇️ Descargar PDF Creado", pdf_bytes, "nuevo_manga.pdf", "application/pdf")
            else:
                st.error("No se encontraron imágenes válidas en el ZIP.")
