import streamlit as st
import fitz  # PyMuPDF
import img2pdf
from PIL import Image, ImageEnhance, ImageStat
import io
import zipfile
import os

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
    [
        "🏠 Inicio", 
        "⚡ Compresor de PDF", 
        "⚡ Compresor de ZIP/CBZ",  # <-- NUEVA OPCIÓN
        "🖼️ Extractor de Imágenes", 
        "✂️ Recortador de Páginas PDF", 
        "🗑️ Limpiador de ZIP/CBZ",
        "📁 Imágenes a PDF (Universal)"
    ]
)

# --- 🏠 PÁGINA DE INICIO ---
if opcion == "🏠 Inicio":
    st.title("Manga PDF Ultimate Toolbox 📚")
    st.write("Suite optimizada para la gestión de archivos de Manga y Novelas.")
    st.info("Selecciona una herramienta a la izquierda.")

# --- ⚡ COMPRESOR DE PDF ---
elif opcion == "⚡ Compresor de PDF":
    st.title("Compresor Inteligente de PDF 🧠")
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
                            img = img.convert("L")
                            img = ImageEnhance.Contrast(img).enhance(1.4)
                            img.save(buf, format="JPEG", quality=70, optimize=True)
                        else:
                            if img.mode != "RGB": img = img.convert("RGB")
                            img.save(buf, format="JPEG", quality=80, optimize=True)
                        imgs_opt.append(buf.getvalue())
                barra.progress((i + 1) / len(doc))
            st.download_button("⬇️ Descargar PDF Optimizado", img2pdf.convert(imgs_opt), f"mini_{archivo.name}", "application/pdf")

# --- ⚡ COMPRESOR DE ZIP/CBZ (NUEVO) ---
elif opcion == "⚡ Compresor de ZIP/CBZ":
    st.title("Compresor Inteligente de ZIP / CBZ ⚡")
    st.write("Aplica la compresión híbrida directamente a tus archivos comprimidos sin pasarlos a PDF.")

    archivo_zip = st.file_uploader("Sube tu archivo ZIP o CBZ pesado", type=["zip", "cbz"])

    if archivo_zip:
        peso_original = archivo_zip.size / (1024 * 1024)
        st.info(f"Peso original del archivo: {peso_original:.2f} MB")

        if st.button("🚀 Aplastar Archivo"):
            barra = st.progress(0)
            texto_estado = st.empty()

            try:
                datos_zip = archivo_zip.read()
                zip_buffer_salida = io.BytesIO()

                paginas_color = 0
                paginas_bn = 0

                # Leemos el ZIP en memoria
                with zipfile.ZipFile(io.BytesIO(datos_zip), 'r') as z_in:
                    lista_imagenes = sorted([f for f in z_in.namelist() if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
                    total_paginas = len(lista_imagenes)

                    if total_paginas == 0:
                        st.error("No se encontraron imágenes válidas para comprimir.")
                    else:
                        # Preparamos el nuevo ZIP
                        with zipfile.ZipFile(zip_buffer_salida, 'w', zipfile.ZIP_DEFLATED) as z_out:
                            for i, filename in enumerate(lista_imagenes):
                                img_bytes = z_in.read(filename)

                                with Image.open(io.BytesIO(img_bytes)) as img:
                                    # 1. Redimensión Inteligente
                                    ancho, alto = img.size
                                    if alto > 1600:
                                        proporcion = 1600 / float(alto)
                                        nuevo_ancho = int(float(ancho) * float(proporcion))
                                        img = img.resize((nuevo_ancho, 1600), Image.Resampling.LANCZOS)

                                    buffer_img = io.BytesIO()

                                    # 2. Análisis Híbrido de Color vs B/N
                                    if es_blanco_y_negro(img):
                                        img = img.convert("L")
                                        potenciador = ImageEnhance.Contrast(img)
                                        img = potenciador.enhance(1.4)
                                        img.save(buffer_img, format="JPEG", quality=70, optimize=True)
                                        paginas_bn += 1
                                    else:
                                        if img.mode in ("RGBA", "P"):
                                            img = img.convert("RGB")
                                        img.save(buffer_img, format="JPEG", quality=80, optimize=True)
                                        paginas_color += 1

                                    # 3. Forzamos la extensión JPEG internamente para ahorrar más
                                    nuevo_nombre = os.path.splitext(filename)[0] + ".jpg"
                                    z_out.writestr(nuevo_nombre, buffer_img.getvalue())

                                # Actualizamos estado en pantalla
                                progreso = (i + 1) / total_paginas
                                barra.progress(progreso)
                                texto_estado.text(f"Procesando página {i + 1} de {total_paginas} (🎨: {paginas_color} | 📄: {paginas_bn})")

                if total_paginas > 0:
                    # Matemáticas finales
                    peso_nuevo = zip_buffer_salida.getbuffer().nbytes / (1024 * 1024)
                    ahorro = 100 - ((peso_nuevo / peso_original) * 100)
                    texto_estado.text("¡Empaquetado finalizado!")

                    st.success(f"¡Listo! El nuevo peso es {peso_nuevo:.2f} MB. Ahorraste un {ahorro:.1f}% de espacio en tu dispositivo.")

                    # Botón de Descarga
                    nombre_base = archivo_zip.name.rsplit('.', 1)[0]
                    st.download_button(
                        label="⬇️ Descargar CBZ Optimizado",
                        data=zip_buffer_salida.getvalue(),
                        file_name=f"{nombre_base}_ligero.cbz",
                        mime="application/zip"
                    )

            except Exception as e:
                st.error(f"Error durante la compresión: {e}")

# --- 🖼️ EXTRACTOR DE IMÁGENES ---
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
                        ext = base_image["ext"]
                        
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

# --- ✂️ RECORTADOR DE PÁGINAS PDF ---
elif opcion == "✂️ Recortador de Páginas PDF":
    st.title("Recortador Visual de PDFs ✂️")
    st.write("Selecciona visualmente las páginas que deseas eliminar.")
    
    archivo = st.file_uploader("Sube el PDF a editar", type=["pdf"])
    
    if archivo:
        doc = fitz.open(stream=archivo.read(), filetype="pdf")
        total_paginas = len(doc)
        st.info(f"El PDF tiene un total de {total_paginas} páginas.")
        
        with st.form("formulario_recorte"):
            st.write("### 🖼️ Galería de Páginas")
            st.caption("Marca la casilla debajo de las páginas que quieres BORRAR.")
            
            columnas = st.columns(4)
            paginas_a_borrar = []
            
            for i in range(total_paginas):
                col_actual = columnas[i % 4]
                with col_actual:
                    pagina = doc[i]
                    pix = pagina.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    
                    st.image(img, use_container_width=True)
                    
                    if st.checkbox(f"🗑️ Borrar Pág {i+1}", key=f"del_{i}"):
                        paginas_a_borrar.append(i)
            
            submit = st.form_submit_button("✂️ Eliminar Páginas Seleccionadas")
            
        if submit:
            if not paginas_a_borrar:
                st.warning("No seleccionaste ninguna página.")
            else:
                nombre_base = archivo.name.rsplit('.', 1)[0]
                nombre_final_recortado = f"{nombre_base}_recortado.pdf"

                for indice in sorted(paginas_a_borrar, reverse=True):
                    doc.delete_page(indice)
                
                buf = io.BytesIO()
                doc.save(buf)
                
                st.success(f"¡Listo! Se eliminaron {len(paginas_a_borrar)} páginas.")
                st.download_button(
                    label=f"⬇️ Descargar {nombre_final_recortado}",
                    data=buf.getvalue(),
                    file_name=nombre_final_recortado,
                    mime="application/pdf"
                )

# --- 🗑️ LIMPIADOR DE ZIP/CBZ ---
elif opcion == "🗑️ Limpiador de ZIP/CBZ":
    st.title("Limpiador Visual de ZIP / CBZ 🗑️")
    st.write("Selecciona visualmente las imágenes que deseas eliminar de tu archivo comprimido.")
    
    archivo_zip = st.file_uploader("Sube el archivo ZIP o CBZ a limpiar", type=["zip", "cbz"])
    
    if archivo_zip:
        try:
            datos_zip = archivo_zip.read()
            
            with zipfile.ZipFile(io.BytesIO(datos_zip), 'r') as z:
                nombres_imagenes = sorted([n for n in z.namelist() if n.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
                total_imagenes = len(nombres_imagenes)
                
                if total_imagenes == 0:
                    st.error("No se encontraron imágenes válidas en este archivo.")
                else:
                    st.info(f"El archivo contiene {total_imagenes} imágenes.")
                    
                    with st.form("formulario_limpieza_zip"):
                        st.write("### 🖼️ Galería de Imágenes")
                        st.caption("Marca la casilla debajo de las páginas que quieres BORRAR.")
                        
                        columnas = st.columns(4)
                        imagenes_a_borrar = []
                        
                        for i, nombre in enumerate(nombres_imagenes):
                            col_actual = columnas[i % 4]
                            with col_actual:
                                img_bytes = z.read(nombre)
                                img = Image.open(io.BytesIO(img_bytes))
                                img.thumbnail((250, 250))
                                
                                st.image(img, use_container_width=True)
                                
                                nombre_corto = (nombre[:15] + '..') if len(nombre) > 15 else nombre
                                
                                if st.checkbox(f"🗑️ Borrar {nombre_corto}", key=f"del_zip_{i}"):
                                    imagenes_a_borrar.append(nombre)
                        
                        submit = st.form_submit_button("✂️ Eliminar Seleccionadas y Crear CBZ")
                        
            if submit:
                if not imagenes_a_borrar:
                    st.warning("No seleccionaste ninguna imagen para eliminar.")
                else:
                    nombre_base = archivo_zip.name.rsplit('.', 1)[0]
                    nombre_final_cbz = f"{nombre_base}_limpio.cbz"
                    
                    zip_buffer_salida = io.BytesIO()
                    
                    with zipfile.ZipFile(io.BytesIO(datos_zip), 'r') as z_in:
                        with zipfile.ZipFile(zip_buffer_salida, 'w', zipfile.ZIP_DEFLATED) as z_out:
                            for nombre in nombres_imagenes:
                                if nombre not in imagenes_a_borrar:
                                    z_out.writestr(nombre, z_in.read(nombre))
                    
                    st.success(f"¡Listo! Se eliminaron {len(imagenes_a_borrar)} páginas.")
                    
                    st.download_button(
                        label=f"⬇️ Descargar {nombre_final_cbz}",
                        data=zip_buffer_salida.getvalue(),
                        file_name=nombre_final_cbz,
                        mime="application/zip"
                    )
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")

# --- 📁 IMÁGENES A PDF ---
elif opcion == "📁 Imágenes a PDF (Universal)":
    st.title("Creador de PDF desde Imágenes 📁")
    st.write("Sube un ZIP o múltiples imágenes para convertirlo en un PDF.")
    
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
        if len(archivos) == 1:
            nombre_base = archivos[0].name.rsplit('.', 1)[0]
        else:
            nombre_base = "manga_recopilacion"
            
        nombre_final_pdf = f"{nombre_base}_pdf.pdf"

        if st.button("Convertir a PDF"):
            imgs_data = []
            barra = st.progress(0)
            
            if len(archivos) == 1 and archivos[0].name.lower().endswith('.zip'):
                with zipfile.ZipFile(archivos[0], "r") as z:
                    nombres = sorted([n for n in z.namelist() if n.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
                    for i, nombre in enumerate(nombres):
                        imgs_data.append(limpiar_transparencia(z.read(nombre)))
                        barra.progress((i + 1) / len(nombres))
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
                        file_name=nombre_final_pdf,
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Error: {e}")
