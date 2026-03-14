use pyo3::prelude::*;

#[pyo3::pymodule]
mod pdftoolsxc_formatter {
    use pyo3::prelude::*;
    use thiserror::Error;

    const A4_WIDTH: u32 = 2480;
    const A4_HEIGHT: u32 = 3508;

    #[derive(Error, Debug)]
    pub enum PdfToolsError {
        #[error("Error de imagen: {0}")]
        ImageError(String),
        #[error("Error de I/O: {0}")]
        IoError(#[from] std::io::Error),
    }

    impl From<PdfToolsError> for PyErr {
        fn from(err: PdfToolsError) -> PyErr {
            pyo3::exceptions::PyRuntimeError::new_err(err.to_string())
        }
    }

    type Result<T> = std::result::Result<T, PdfToolsError>;

    #[pyfunction]
    fn scale_to_a4(input: String, output: String) -> PyResult<String> {
        let path = std::path::Path::new(&input);
        if !path.exists() {
            return Err(PdfToolsError::ImageError(format!("Archivo no encontrado: {}", input)).into());
        }
        
        let img = image::ImageReader::open(path)
            .map_err(|e| PdfToolsError::ImageError(format!("Error al abrir imagen: {}", e)))?
            .decode()
            .map_err(|e| PdfToolsError::ImageError(format!("Error al decodificar imagen: {}", e)))?;
        
        let (orig_width, orig_height) = (img.width(), img.height());
        
        let scale_x = A4_WIDTH as f64 / orig_width as f64;
        let scale_y = A4_HEIGHT as f64 / orig_height as f64;
        let scale = scale_x.min(scale_y);
        
        let new_width = (orig_width as f64 * scale) as u32;
        let new_height = (orig_height as f64 * scale) as u32;
        
        let resized = img.resize_exact(
            new_width.max(1),
            new_height.max(1),
            image::imageops::FilterType::Lanczos3,
        );
        
        std::fs::create_dir_all(std::path::Path::new(&output).parent().unwrap()).ok();
        
        resized.save(&output)
            .map_err(|e| PdfToolsError::ImageError(format!("Error al guardar: {}", e)))?;
        
        Ok(format!("Imagen escalada a A4: {}x{} -> {}x{}", orig_width, orig_height, new_width, new_height))
    }

    #[pyfunction]
    fn compress_image(input: String, output: String, quality: u8) -> PyResult<String> {
        let path = std::path::Path::new(&input);
        if !path.exists() {
            return Err(PdfToolsError::ImageError(format!("Archivo no encontrado: {}", input)).into());
        }
        
        let img = image::ImageReader::open(path)
            .map_err(|e| PdfToolsError::ImageError(format!("Error al abrir imagen: {}", e)))?
            .decode()
            .map_err(|e| PdfToolsError::ImageError(format!("Error al decodificar imagen: {}", e)))?;
        
        let (width, height) = (img.width(), img.height());
        
        let target_quality = quality as f64 / 100.0;
        let new_width = ((width as f64) * target_quality) as u32;
        let new_height = ((height as f64) * target_quality) as u32;
        
        let resized = img.resize_exact(
            new_width.max(1),
            new_height.max(1),
            image::imageops::FilterType::Lanczos3,
        );
        
        std::fs::create_dir_all(std::path::Path::new(&output).parent().unwrap()).ok();
        
        resized.save(&output)
            .map_err(|e| PdfToolsError::ImageError(format!("Error al guardar: {}", e)))?;
        
        Ok(format!("Imagen comprimida: {}x{} -> {}x{} (quality: {}%)", 
            width, height, new_width, new_height, quality))
    }

    #[pyfunction]
    fn resize_image(input: String, output: String, width: u32, height: u32) -> PyResult<String> {
        let path = std::path::Path::new(&input);
        if !path.exists() {
            return Err(PdfToolsError::ImageError(format!("Archivo no encontrado: {}", input)).into());
        }
        
        let img = image::ImageReader::open(path)
            .map_err(|e| PdfToolsError::ImageError(format!("Error al abrir imagen: {}", e)))?
            .decode()
            .map_err(|e| PdfToolsError::ImageError(format!("Error al decodificar imagen: {}", e)))?;
        
        let resized = img.resize_exact(
            width.max(1),
            height.max(1),
            image::imageops::FilterType::Lanczos3,
        );
        
        std::fs::create_dir_all(std::path::Path::new(&output).parent().unwrap()).ok();
        
        resized.save(&output)
            .map_err(|e| PdfToolsError::ImageError(format!("Error al guardar: {}", e)))?;
        
        Ok(format!("Imagen redimensionada a {}x{}", width, height))
    }
}
