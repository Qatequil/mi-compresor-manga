import streamlit as st
import fitz  # PyMuPDF
import img2pdf
from PIL import Image, ImageEnhance, ImageStat
import io

# Configuración de la página web
st.set_page_config(page_title="Compresor Manga Pro", page_icon="📚", layout="centered")


def es_blanco_y_negro(img):
    if img.mode in ("L", "1"):
        return True
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    hsv_img = img.convert('HSV')
    banda_saturacion = hsv_img.split()[1]
    estadisticas = ImageStat.Stat(banda_saturacion)
    max_saturacion = estadisticas.extrema[0][1]
    return max_saturacion < 15


# --- INTERFAZ WEB ---
st.title("Compresor Inteligente de Manga 📚⚡")
st.write(
    "Sube tu PDF pesado. Detectaremos automáticamente las portadas a color y comprimiremos brutalmente las páginas en blanco y negro.")

# Caja para subir archivos
archivo_subido = st.file_uploader("Arrastra tu PDF aquí", type=["pdf"])

if archivo_subido is not None:
    st.success(f"Archivo cargado: {archivo_subido.name}")
    peso_original = archivo_subido.size / (1024 * 1024)
    st.info(f"Peso original: {peso_original:.2f} MB")

    # Botón mágico
    if st.button("¡Comprimir PDF ahora!"):

        # Barra de progreso para que el usuario no se desespere
        barra_progreso = st.progress(0)
        texto_estado = st.empty()

        try:
            # En web, leemos el PDF directamente desde la memoria (Bytes)
            doc = fitz.open(stream=archivo_subido.read(), filetype="pdf")
            imagenes_optimizadas = []
            total_paginas = len(doc)

            paginas_color = 0
            paginas_bn = 0

            for num_pagina in range(total_paginas):
                pagina = doc[num_pagina]
                lista_imagenes = pagina.get_images(full=True)

                if lista_imagenes:
                    xref = lista_imagenes[0][0]
                    base_image = doc.extract_image(xref)
                    bytes_imagen = base_image["image"]

                    with Image.open(io.BytesIO(bytes_imagen)) as img:
                        # Redimensión máxima a 1600px de alto
                        ancho, alto = img.size
                        if alto > 1600:
                            proporcion = 1600 / float(alto)
                            nuevo_ancho = int(float(ancho) * float(proporcion))
                            img = img.resize((nuevo_ancho, 1600), Image.Resampling.LANCZOS)

                        buffer_salida = io.BytesIO()

                        # Lógica Híbrida
                        if es_blanco_y_negro(img):
                            img = img.convert("L")
                            potenciador = ImageEnhance.Contrast(img)
                            img = potenciador.enhance(1.4)
                            img.save(buffer_salida, format="JPEG", quality=70, optimize=True)
                            paginas_bn += 1
                        else:
                            if img.mode in ("RGBA", "P"):
                                img = img.convert("RGB")
                            img.save(buffer_salida, format="JPEG", quality=80, optimize=True)
                            paginas_color += 1

                        imagenes_optimizadas.append(buffer_salida.getvalue())

                # Actualizar barra de progreso web
                progreso = (num_pagina + 1) / total_paginas
                barra_progreso.progress(progreso)
                texto_estado.text(
                    f"Procesando página {num_pagina + 1} de {total_paginas}... (🎨 Color: {paginas_color} | 📄 B/N: {paginas_bn})")

            # Armar PDF Final en memoria
            if imagenes_optimizadas:
                texto_estado.text("¡Empaquetando nuevo PDF...!")
                pdf_final_bytes = img2pdf.convert(imagenes_optimizadas)

                peso_nuevo = len(pdf_final_bytes) / (1024 * 1024)
                ahorro = 100 - ((peso_nuevo / peso_original) * 100)

                st.success(
                    f"¡Terminado! El nuevo peso es {peso_nuevo:.2f} MB. Te ahorraste un {ahorro:.1f}% de espacio.")

                # BOTÓN DE DESCARGA WEB
                st.download_button(
                    label="⬇️ Descargar PDF Comprimido",
                    data=pdf_final_bytes,
                    file_name=archivo_subido.name.replace(".pdf", "_Mini.pdf"),
                    mime="application/pdf"
                )
            else:
                st.error("No se encontraron imágenes en el PDF.")

        except Exception as e:
            st.error(f"Ocurrió un error: {e}")