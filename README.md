# ManTuls - Digital Productivity Suite

ManTuls is an internal comprehensive office productivity tool suite developed for LMAN (Lembaga Manajemen Aset Negara). It provides a unified interface for various document processing tasks, enhanced with AI capabilities and secure SSO integration.

![ManTuls Screenshot](./frontend/public/icon.png)

## 🚀 Features

### Document Tools
- **PDF Tools**: Merge, Split, Compress, Watermark, Protect/Unlock PDF.
- **Conversion**: PDF to Word, Word to PDF.
- **OCR Scanner**: Extract text from images and PDFs using AI.
- **Image Tools**: Remove Background (AI), Image Converter, QR Code Generator.

### Key Highlights
- **SSO Integration**: Secure login using LMAN SSO credential with JWT session management.
- **Modern UI**: Neo-brutalist distinct design language.
- **Production Ready**: Optimized Docker support for easy deployment.
- **Privacy First**: Self-hosted solution ensuring document data stays within the internal network.

## 🛠 Tech Stack

- **Frontend**: Nuxt 3 (Vue.js), TailwindCSS (Custom Design System).
- **Backend**: Python FastAPI, Hue (Lightweight worker).
- **AI/Processing**: PaddleOCR, Rembg, OpenAI (Optional), LibreOffice, PDF2Docx.
- **Infrastructure**: Docker Compose.

## 🏁 Getting Started

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local dev)
- Python 3.10+ (for local dev)

### Local Development

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd OCR_services
   ```

2. **Setup Environment**
   Copy `.env.example` to `.env` (create one if missing):
   ```
   OCR_SECRET_KEY=dev-secret-key
   JWT_SECRET=dev-jwt-secret
   ```

3. **Run with Docker (Recommended)**
   ```bash
   docker compose up -d
   ```
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000
   - Docs: http://localhost:8000/docs

### 📦 Production Deployment

1. **Configure Production Env**
   Create a `.env` file on the production server:
   ```env
   OCR_SECRET_KEY=your-secure-random-key
   JWT_SECRET=your-secure-jwt-secret
   ```

2. **Deploy**
   Use the provided helper script:
   ```bash
   chmod +x deploy_prod.sh
   ./deploy_prod.sh http://your-server-ip:8003
   ```
   
   Or manually:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

   - **Production Frontend**: Port 3003
   - **Production Backend**: Port 8003

## 🔒 Security

- **Authentication**: All tools are protected behind SSO Login.
- **Secrets**: API Keys and config files are excluded from Git (`.gitignore`).
- **Data Retention**: Models are persisted, but uploaded files are temporary (container lifespan).

## 📝 License

Internal Use Only - IT LMAN.
Crafted by I.A.
