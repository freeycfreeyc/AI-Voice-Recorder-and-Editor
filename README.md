# 🎙️ ClearScript AI: Smart Audio Transcriber & Refiner
ClearScript AI is a powerful desktop application that transforms raw audio into polished, professional text. By combining OpenAI Whisper's local speech-to-text capabilities with Google Gemini's advanced linguistic intelligence, it automates the process of transcribing and refining lectures, meetings, and interviews.

ClearScript AI는 가공되지 않은 음성 파일을 깨끗하고 전문적인 텍스트로 변환해 주는 스마트 전사 및 정제 도구입니다. OpenAI Whisper를 통한 고성능 로컬 음성 인식과 Google Gemini의 문맥 파악 능력을 결합하여, 단순히 받아쓰는 것을 넘어 문맥에 맞게 다듬어진 완벽한 스크립트를 제공합니다.

# ✨ 주요 기능 (Key Features)
Smart Transcription (Local): OpenAI Whisper (Small) 모델을 사용하여 클라우드 업로드 없이 로컬에서 안전하게 음성을 텍스트로 변환합니다.

AI-Powered Refinement: Gemini 2.5 Flash API가 변환된 텍스트의 오탈자 교정, 문단 나누기, 적절한 구두점 삽입을 자동으로 수행합니다.

Context-Aware Processing: 사용자가 입력한 '핵심 키워드'나 '상황 설명'을 바탕으로 전문 용어나 고유 명사를 정확하게 교정합니다.

Modern Desktop Experience: CustomTkinter 기반의 다크 모드 UI와 파일 드래그 앤 드롭(Drag & Drop) 기능을 지원합니다.

GPU Accelerated: NVIDIA GPU(CUDA) 가속을 지원하여 대용량 파일도 빠르게 처리할 수 있습니다.

# 🇺🇸 English Introduction
ClearScript AI goes beyond simple dictation. It bridges the gap between raw speech and readable content by leveraging a dual-AI pipeline.

# ✨ Key Features
Local STT Engine: Uses OpenAI Whisper (Small) to transcribe audio locally on your machine, ensuring privacy and cost-efficiency.

Intelligent Correction: Sends transcribed text to Google Gemini API to fix typos, apply proper spacing, and improve overall readability.

Direct Instruction: Users can provide 'context hints' or 'keywords' to guide the AI in handling specialized terminology or names.

User-Friendly GUI: Features a sleek dark-mode interface built with CustomTkinter and seamless file Drag & Drop support.

# 🛠️ 기술 스택 (Tech Stack)
Language: Python 3.11

STT Engine: OpenAI Whisper (Local, Small Model)

Refinement Engine: Google Gemini 2.5 Flash API

GUI: CustomTkinter, TkinterDnD2

Build: PyInstaller (with GPU/CUDA support)

# 🚀 시작하기 (Getting Started)
1. 필수 요구사항 (Prerequisites)
이 프로그램은 음성 데이터 처리를 위해 FFmpeg가 반드시 필요합니다.

Windows: winget install ffmpeg

Mac: brew install ffmpeg

2. API 키 설정 (API Key)
문맥 교정 기능을 위해 Google Gemini API 키가 필요합니다. Google AI Studio에서 무료로 발급받을 수 있습니다.

3. 설치 및 실행 (Installation)
Bash
# Clone the repository
git clone https://github.com/freeycfreeyc/ClearScript-AI.git

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
📦 배포 (Distribution)
NVIDIA GPU 가속을 지원하는 단일 실행 파일(.exe) 버전입니다. 별도의 파이썬 설치 없이 즉시 사용할 수 있습니다.

👉 최신 버전 다운로드 (Google Drive)

참고: AI 엔진 및 GPU 라이브러리 포함으로 인해 용량이 약 2.7GB입니다.
