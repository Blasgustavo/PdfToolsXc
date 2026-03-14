"""Wrapper Python para la extensión Rust formatter"""

from pathlib import Path
from typing import Iterable, List

import os
import shutil
import tempfile


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def _fit_to_a4_rgb(img, a4_w_px: int, a4_h_px: int):
    from PIL import Image

    pil_img = img.convert("RGB")
    src_w, src_h = pil_img.size
    scale_fit = min(a4_w_px / max(1, src_w), a4_h_px / max(1, src_h))
    dst_w = max(1, int(round(src_w * scale_fit)))
    dst_h = max(1, int(round(src_h * scale_fit)))
    resized = pil_img.resize((dst_w, dst_h), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (a4_w_px, a4_h_px), (255, 255, 255))
    off_x = (a4_w_px - dst_w) // 2
    off_y = (a4_h_px - dst_h) // 2
    canvas.paste(resized, (off_x, off_y))
    return canvas


def process_files(inputs: List[str], output: str, quality: int = 85) -> str:
    """Procesa multiples archivos (PDF/imagenes) y devuelve un solo PDF A4.

    - Cada pagina de cada PDF se convierte a imagen
    - Cada imagen se ajusta a A4 sin deformar (letterbox)
    - Todo se une en un solo `*_updated.pdf`
    """
    import pypdfium2 as pdfium
    from fpdf import FPDF
    from PIL import Image

    q = _clamp(int(quality), 10, 100)

    # DPI objetivo: mejora nitidez vs. el original sin inflar demasiado el peso.
    # 10 -> 180dpi, 85 -> ~230dpi, 100 -> 240dpi
    target_dpi = int(180 + (q - 10) * (60.0 / 90.0))
    target_dpi = _clamp(target_dpi, 180, 240)

    # JPEG quality: suficiente para texto/lineas sin disparar tanto el peso.
    # 10 -> 75, 85 -> ~85, 100 -> 88
    jpeg_quality = int(75 + (q - 10) * (13.0 / 90.0))
    jpeg_quality = _clamp(jpeg_quality, 75, 88)

    # Subsampling: 0 = 4:4:4, 1 = 4:2:2, 2 = 4:2:0
    if q >= 90:
        jpeg_subsampling = 0
    elif q >= 70:
        jpeg_subsampling = 1
    else:
        jpeg_subsampling = 2

    a4_w_px = int(round(8.27 * target_dpi))
    a4_h_px = int(round(11.69 * target_dpi))
    render_scale = target_dpi / 72.0

    tmp_dir = Path(tempfile.mkdtemp(prefix="pdftoolsxc_"))
    try:
        out_pdf = FPDF(orientation="P", unit="mm", format="A4")
        out_pdf.set_auto_page_break(False)

        page_idx = 0
        for file_path in inputs:
            path = Path(file_path)
            ext = path.suffix.lower()

            if ext == ".pdf":
                doc = pdfium.PdfDocument(str(path))
                for n in range(len(doc)):
                    page = doc[n]
                    bitmap = page.render(scale=render_scale, optimize_mode="print")
                    pil_img = bitmap.to_pil()
                    canvas = _fit_to_a4_rgb(pil_img, a4_w_px, a4_h_px)

                    page_idx += 1
                    jpg_path = tmp_dir / f"page_{page_idx:06}.jpg"
                    canvas.save(
                        str(jpg_path),
                        format="JPEG",
                        quality=jpeg_quality,
                        optimize=True,
                        progressive=True,
                        subsampling=jpeg_subsampling,
                        dpi=(target_dpi, target_dpi),
                    )

                    out_pdf.add_page()
                    out_pdf.image(str(jpg_path), x=0, y=0, w=210, h=297)
            else:
                pil_img = Image.open(str(path))
                canvas = _fit_to_a4_rgb(pil_img, a4_w_px, a4_h_px)

                page_idx += 1
                jpg_path = tmp_dir / f"page_{page_idx:06}.jpg"
                canvas.save(
                    str(jpg_path),
                    format="JPEG",
                    quality=jpeg_quality,
                    optimize=True,
                    progressive=True,
                    subsampling=jpeg_subsampling,
                    dpi=(target_dpi, target_dpi),
                )

                out_pdf.add_page()
                out_pdf.image(str(jpg_path), x=0, y=0, w=210, h=297)

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        out_pdf.output(str(output_path))
        return str(output_path)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def process_pdf(input: str, output: str, quality: int = 85) -> str:
    """Procesa PDF: render -> A4 -> PDF (calidad/size balance).

    - Renderiza cada pagina con PDFium (pypdfium2)
    - Redimensiona a A4 a un DPI derivado de `quality`
    - Recomprime a JPEG y compone un PDF A4 via fpdf2
    """
    return process_files([input], output, quality=quality)


def extract_images(input: str, output_dir: str) -> List[str]:
    """Extrae todas las imágenes de un PDF"""
    import pypdfium2 as pdfium
    
    pdf = pdfium.PdfDocument(input)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    extracted = []
    
    for page_idx, page in enumerate(pdf):
        page_images = page.get_images()
        
        for img_idx, img_data in enumerate(page_images):
            file_name = f"page{page_idx+1}_img{img_idx+1}.png"
            img_path = output_path / file_name
            
            img_data[0].save(img_path)
            extracted.append(str(img_path))
    
    return extracted


def scale_to_a4(input: str, output: str) -> str:
    """Escala una imagen a formato A4 (2480x3508)"""
    from pdftoolsxc_formatter import scale_to_a4 as _scale
    return _scale(input, output)


def compress_image(input: str, output: str, quality: int = 85) -> str:
    """Comprime una imagen con la calidad especificada"""
    from pdftoolsxc_formatter import compress_image as _compress
    return _compress(input, output, quality)


def render_pdf(input: str, output_dir: str, dpi: int = 300) -> List[str]:
    """Renderiza un PDF a imágenes"""
    import pypdfium2 as pdfium
    
    pdf = pdfium.PdfDocument(input)
    scale = dpi / 72.0
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    rendered = []
    
    for page_num in range(len(pdf)):
        page = pdf[page_num]
        
        bitmap = page.render(scale=scale)
        pil_img = bitmap.to_pil()
        
        page_output = output_path / f"page_{page_num+1:04}.png"
        pil_img.save(page_output)
        
        rendered.append(str(page_output))
        print(f"Rendered page {page_num+1}/{len(pdf)}")
    
    return rendered


def get_pdf_info(input: str) -> str:
    """Obtiene información de un PDF"""
    import pypdfium2 as pdfium
    
    pdf = pdfium.PdfDocument(input)
    page_count = len(pdf)
    
    return f'{{"pages": {page_count}}}'
