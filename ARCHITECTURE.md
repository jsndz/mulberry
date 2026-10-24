# Mulberry Architecture

This document provides architectural references for the Mulberry project.

## Subsystems

- **Processing Engine (`processing/`)**: Complete HCD-HTR pipeline for handwritten notes, multi-page PDFs, RAW image ingestion, diagram segmentation, and Markdown/PDF document exports.
  - Full Architecture Documentation: [processing/ARCHITECTURE.md](file:///home/jsndz/code/projects/mulberry/processing/ARCHITECTURE.md)
  - Processing Design Specification: [docs/extract_design.md](file:///home/jsndz/code/projects/mulberry/docs/extract_design.md)
  - System Design Specification: [docs/system_design.md](file:///home/jsndz/code/projects/mulberry/docs/system_design.md)

- **Application Frontend & Desktop Shell (`src/`, `src-tauri/`)**:
  - Tauri + Rust native desktop container
  - React/TypeScript user interface
