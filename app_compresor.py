import streamlit as st
import fitz  # PyMuPDF
import img2pdf
from PIL import Image, ImageEnhance, ImageStat
import io
import zipfile

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Manga PDF Toolbox", page_icon="📚", layout="wide")

# --- FUNCIONES LÓGICAS ---

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
    ["🏠 Inicio", "⚡ Compresor Inteligente", "🖼️ Extractor de Imágenes", "✂️ Recortador de Páginas", "📁 Imágenes a PDF (Múltiple)"]
)

# --- 🏠 PÁGINA DE INICIO ---
if opcion == "🏠 Inicio":
    st.title("Manga PDF Ultimate Toolbox 📚")
    st.write("Suite optimizada para la gestión de archivos de Manga y Novelas.")
    st.info("Selecciona una herramienta a la izquierda.")

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
                        if img.height > 1600:
                            img = img.resize((int(img.width * (1600/img.height)), 1600), Image.Resampling.LANCZOS)
                        buf = io.BytesIO()
                        if es_blanco_y_negro(img):
                            img = img.convert("L"); img = ImageEnhance.Contrast(img).enhance(1.4)
                            img.save(buf, format="JPEG", quality=70, optimize=True)
                        else:
                            if img.mode != "RGB": img = img.convert("RGB")
                            img.save(buf, format="JPEG", quality=80, optimize=True)
                        imgs_opt.append(buf.getvalue())
                barra.progress((i + 1) / len(doc))
            st.download_button("⬇️ Descargar PDF Optimizado", img2pdf.convert(imgs_opt), f"mini_{archivo.name}", "application/pdf")

# --- 🖼️ EXTRACTOR DE IMÁGENES (NUEVO) ---
elif opcion == "🖼️ Extractor de Imágenes":
    st.title("Extractor de Imágenes Originales 🖼️")
    st.write("Extrae las imágenes puras del PDF (sin márgenes de página) en un archivo ZIP ordenado.")
    
    archivo_pdf = st.file_uploader("Sube el PDF para extraer imágenes", type=["pdf"])
    
    if archivo_pdf:
        if st.button("Extraer y Organizar"):
            doc = fitz.open(stream=archivo_pdf.read(), filetype="pdf")
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zf:
                contador = 0
                barra = st.progress(0)
                
                for num_pag in range(len(doc)):
                    lista_imgs = doc.get_page_images(num_pag)
                    
                    for img_info in lista_imgs:
                        xref = img_info[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        ext = base_image["ext"] # png, jpeg, etc.
                        
                        # Nombre con formato 000, 001, 002...
                        nombre_archivo = f"{contador:03d}.{ext}"
                        zf.writestr(nombre_archivo, image_bytes)
                        contador += 1
                        
                    barra.progress((num_pag + 1) / len(doc))
            
            st.success(f"¡Extracción completa! Se encontraron {contador} imágenes.")
            st.download_button(
                label="⬇️ Descargar ZIP con Imágenes",
                data=zip_buffer.getvalue(),
                file_name=f"imagenes_{archivo_pdf.name.replace('.pdf', '')}.zip",
                mime="application/zip"
            )

# --- ✂️ RECORTADOR DE PÁGINAS ---
elif opcion == "✂️ Recortador de Páginas":
    st.title("Recortador de PDFs ✂️")
    archivo = st.file_uploader("Sube el PDF a editar", type=["pdf"])
    paginas_input = st.text_input("Páginas a BORRAR (ej: 1, 3, 5)")
    if archivo and paginas_input:
        if st.button("Eliminar Páginas"):
            doc = fitz.open(stream=archivo.read(), filetype="pdf")
            indices = [int(x.strip()) - 1 for x in paginas_input.split(",")]
            for indice in sorted(indices, reverse=True):
                if 0 <= indice < len(doc): doc.delete_page(indice)
            buf = io.BytesIO(); doc.save(buf)
            st.download_button("⬇️ Descargar PDF Recortado", buf.getvalue(), f"editado_{archivo.name}", "application/pdf")

# --- 📁 IMÁGENES A PDF (UNIVERSAL) ---
elif opcion == "📁 Imágenes a PDF (Múltiple)":
    st.title("Creador de PDF desde Imágenes 📁")
    st.write("Ideal para móvil: Sube un solo **ZIP** o selecciona **múltiples imágenes**.")
    
    # Añadimos "zip" a los tipos permitidos
    archivos = st.file_uploader(
        "Sube tus archivos aquí", 
        type=["zip", "jpg", "png", "jpeg", "webp"], 
        accept_multiple_files=True
    )
    
    if archivos:
        if st.button("Convertir a PDF"):
            imgs_data = []
            
            # Caso A: El usuario subió un solo archivo y es un ZIP
            if len(archivos) == 1 and archivos[0].name.lower().endswith('.zip'):
                st.info("Detectado archivo ZIP. Extrayendo imágenes...")
                with zipfile.ZipFile(archivos[0], "r") as z:
                    # Filtramos solo imágenes y ordenamos por nombre
                    nombres = sorted([
                        n for n in z.namelist() 
                        if n.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
                    ])
                    for nombre in nombres:
                        imgs_data.append(z.read(nombre))
            
            # Caso B: El usuario subió imágenes sueltas (una o varias)
            else:
                st.info(f"Procesando {len(archivos)} imágenes sueltas...")
                # Ordenamos por nombre de archivo para mantener el orden del manga
                archivos_ordenados = sorted(archivos, key=lambda x: x.name)
                for f in archivos_ordenados:
                    imgs_data.append(f.read())
            
            if imgs_data:
                # Convertimos la lista de bytes de imagen a un solo PDF
                pdf_bytes = img2pdf.convert(imgs_data)
                st.success("¡PDF generado con éxito!")
                st.download_button(
                    label="⬇️ Descargar PDF",
                    data=pdf_bytes,
                    file_name="manga_final.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("No se encontraron imágenes válidas. Asegúrate de que el ZIP contenga fotos JPG o PNG.")
