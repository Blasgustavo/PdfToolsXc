# PdfToolsXc

Herramientas PDF con Python + Rust

## Características

- **Compresión de PDFs**: Reduce el tamaño de archivos PDF manteniendo la calidad
- **Unión de PDFs**: Combina múltiples archivos PDF en uno solo
- **División de PDFs**: Separa un PDF en múltiples archivos
- **OCR**: Reconocimiento óptico de caracteres
- **Organizador de páginas**: Reordena, rota y elimina páginas

## Requisitos

- Python 3.11+
- Rust (para el módulo formatter)

## Instalación

```bash
# Instalar dependencias Python
pip install -e .

# Compilar el módulo Rust
pip install maturin
maturin develop
```

## Uso

```bash
python main.py
```

## Licencia

MIT
