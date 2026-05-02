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
    ["🏠 Inicio", "⚡ Compresor Inteligente", "🖼️ Extractor de Imágenes", "✂️ Recortador de Páginas", "📁 Imágenes a PDF (Universal)"]
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

# --- ✂️ RECORTADOR DE PÁGINAS (VERSIÓN VISUAL PRO) ---
elif opcion == "✂️ Recortador de Páginas":
    st.title("Recortador Visual de PDFs ✂️")
    st.write("Selecciona visualmente las páginas que deseas eliminar (ideal para quitar créditos o portadas dobles).")
    
    archivo = st.file_uploader("Sube el PDF a editar", type=["pdf"])
    
    if archivo:
        # Abrimos el PDF original
        doc = fitz.open(stream=archivo.read(), filetype="pdf")
        total_paginas = len(doc)
        st.info(f"El PDF tiene un total de {total_paginas} páginas.")
        
        # st.form evita que la página se recargue cada vez que haces clic en una casilla
        with st.form("formulario_recorte"):
            st.write("### 🖼️ Galería de Páginas")
            st.caption("Marca la casilla debajo de las páginas que quieres BORRAR.")
            
            # Creamos una cuadrícula de 4 columnas para que parezca una galería
            columnas = st.columns(4)
            paginas_a_borrar = []
            
            # Generamos las miniaturas
            for i in range(total_paginas):
                col_actual = columnas[i % 4] # Esto reparte las imágenes entre las 4 columnas
                with col_actual:
                    # Extraemos la página en calidad muy baja (0.2) para que cargue súper rápido
                    pagina = doc[i]
                    pix = pagina.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    
                    st.image(img, use_container_width=True)
                    
                    # Si el usuario marca esta casilla, guardamos el número 'i'
                    if st.checkbox(f"🗑️ Borrar Pág {i+1}", key=f"del_{i}"):
                        paginas_a_borrar.append(i)
            
            # El botón final del formulario
            submit = st.form_submit_button("✂️ Eliminar Páginas Seleccionadas")
            
        # Cuando el usuario presiona el botón del formulario
        # Cuando el usuario presiona el botón del formulario
        if submit:
            if not paginas_a_borrar:
                st.warning("No seleccionaste ninguna página.")
            else:
                # 1. Extraemos el nombre base igual que hicimos con el conversor
                nombre_base = archivo.name.rsplit('.', 1)[0]
                nombre_final_recortado = f"{nombre_base}_recortado.pdf"

                # 2. Operación de borrado
                for indice in sorted(paginas_a_borrar, reverse=True):
                    doc.delete_page(indice)
                
                buf = io.BytesIO()
                doc.save(buf)
                
                st.success(f"¡Listo! Se eliminaron {len(paginas_a_borrar)} páginas.")
                
                # 3. Botón con el nombre corregido
                st.download_button(
                    label=f"⬇️ Descargar {nombre_final_recortado}",
                    data=buf.getvalue(),
                    file_name=nombre_final_recortado, # <-- Aquí aplica el nombre que pediste
                    mime="application/pdf"
                )
                
# --- 📁 IMÁGENES A PDF (CON NOMBRE DINÁMICO) ---
elif opcion == "📁 Imágenes a PDF (Universal)":
    st.title("Creador de PDF desde Imágenes 📁")
    st.write("Sube un ZIP o múltiples imágenes. Para convertirlo en un PDF")
    
    archivos = st.file_uploader(
        "Sube tus archivos aquí", 
        type=["zip", "jpg", "png", "jpeg", "webp"], 
        accept_multiple_files=True
    )
    
    def limpiar_transparencia(bytes_img):
        try:
            with Image.open(io.BytesIO(bytes_img)) as img:
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    fondo = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P": img = img.convert("RGBA")
                    fondo.paste(img, mask=img.split()[-1]) 
                    buf = io.BytesIO()
                    fondo.save(buf, format="JPEG", quality=95)
                    return buf.getvalue()
                return bytes_img
        except:
            return bytes_img
            
    if archivos:
        # --- LÓGICA PARA EL NOMBRE DEL ARCHIVO ---
        if len(archivos) == 1:
            # Si es un solo archivo (como un ZIP), tomamos su nombre y quitamos la extensión
            nombre_base = archivos[0].name.rsplit('.', 1)[0]
        else:
            # Si son imágenes sueltas, usamos el nombre de la primera o un genérico
            nombre_base = "manga_recopilacion"
            
        nombre_final_pdf = f"{nombre_base}_pdf.pdf"

        if st.button("Convertir a PDF"):
            imgs_data = []
            barra = st.progress(0)
            
            # Caso A: Archivo ZIP
            if len(archivos) == 1 and archivos[0].name.lower().endswith('.zip'):
                with zipfile.ZipFile(archivos[0], "r") as z:
                    nombres = sorted([n for n in z.namelist() if n.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
                    for i, nombre in enumerate(nombres):
                        imgs_data.append(limpiar_transparencia(z.read(nombre)))
                        barra.progress((i + 1) / len(nombres))
            
            # Caso B: Imágenes Sueltas
            else:
                archivos_ordenados = sorted(archivos, key=lambda x: x.name)
                for i, f in enumerate(archivos_ordenados):
                    imgs_data.append(limpiar_transparencia(f.read()))
                    barra.progress((i + 1) / len(archivos_ordenados))
            
            if imgs_data:
                try:
                    pdf_bytes = img2pdf.convert(imgs_data)
                    st.success(f"¡PDF '{nombre_final_pdf}' generado!")
                    st.download_button(
                        label=f"⬇️ Descargar {nombre_final_pdf}",
                        data=pdf_bytes,
                        file_name=nombre_final_pdf, # Aquí aplicamos el nombre dinámico
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Error: {e}")
