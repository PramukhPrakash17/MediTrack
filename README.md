# 🏥 MediTrack – AI-Powered Doctor Insight Application

MediTrack is a healthcare-focused application designed to **simplify patient record management** by leveraging **retrieval-augmented generation, fine-tuned computer vision, and AI-powered document processing**. Built with **Spring Boot**, **Spring AI**, a **fine-tuned YOLOv8 model**, **Document AI**, and **Gemini 1.5 Pro**, it provides doctors with dataset-grounded answers, automated image detection, structured dashboards, and secure access to patient data.

---

### Key Features

- **Symptom-Based Clinical RAG** for grounded, hallucination-free Q&A over a medical encyclopedia.
- **Agentic Drug-Information RAG** for natural-language drug queries resolved against a structured drug dataset.
- **Fine-Tuned YOLOv8 X-ray Analysis** for automated image-based detection.
- **Document AI Integration** for automated extraction from lab reports and medical scans.
- **AI-Powered Summaries** with Gemini 1.5 Pro for patient history insights.
- **Doctor Dashboard** – clear and organized view of patient history.
- **Secure System** with JWT authentication and secured endpoints.

---

## 🧩 System Components

### 1. 📚 Symptom-Based Clinical RAG *(Spring Boot + Spring AI)*
- Embeds a medical encyclopedia into **PGVector** and retrieves relevant sections using **Ollama** embeddings.
- Expands user queries with domain-specific keywords (symptoms, causes, treatment, diagnosis, prognosis) before retrieval to improve section matching.
- Applies a **similarity threshold** to filter out low-relevance chunks, and returns a clear "not enough information" response instead of hallucinating when nothing relevant is found.
- Uses **Groq (Llama 3.1)** to generate concise answers that stay strictly grounded in retrieved PDF context, preserving original wording rather than freely paraphrasing.

### 2. 💊 Agentic Drug-Information RAG *(Spring Boot + Spring AI)*
- **Agentic extraction step** parses the doctor's natural-language question to identify the drug name and relevant document types.
- **Multi-stage drug resolution**: exact match → normalized name match → fallback formulation match, handling variations in dosage/form naming.
- Retrieves **metadata-filtered vector context** (drug name + document type) rather than relying on semantic similarity alone.
- LLM prompt is strictly grounded — answers only from the "Primary Drug Information" section, with few-shot examples guiding natural, doctor-facing phrasing instead of robotic dataset echoes.

### 3. 🩻 X-ray Analysis Service *(Python + YOLOv8, in progress)*
- Fine-tuning a **YOLOv8** model on a labeled X-ray image dataset for automated detection.
- Includes dataset preparation, validation, and multiple training experiments across resolutions (640px, 1024px) to optimize detection accuracy.
- Being integrated as a complementary imaging-analysis service alongside the existing document and RAG pipelines.

### 4. 📑 Document AI Processor
- Extracts data from **lab reports, prescriptions, and scans**.
- Uses **custom processors** and **fine-tuning with labeled samples**.
- Automates unstructured-to-structured data conversion.

### 5. 🤖 AI Summarization (Gemini 1.5 Pro)
- Generates concise patient summaries.
- Reduces manual review burden.
- Handles large datasets with efficiency.

### 6. 🩺 Doctor Dashboard
- Provides a unified view of patient records.
- Displays AI-generated patient history summaries.
- Saves doctor's time and improves decision-making.

### 7. 🔐 Security Layer
- **JWT Tokens** for authentication.
- **Secured API endpoints**.

---

## 🔧 Technologies Used

| Tech / Service       | Description                                              |
|-----------------------|-----------------------------------------------------------|
| Spring Boot           | Backend framework for APIs & services                    |
| Spring AI             | RAG orchestration, vector search, and LLM integration     |
| PGVector              | Vector storage for embedded medical & drug documents      |
| Ollama                | Local embedding generation for the symptom RAG service    |
| Groq (Llama 3.1)      | LLM inference for grounded, dataset-strict responses      |
| YOLOv8 (Python)       | Fine-tuned object detection for X-ray image analysis      |
| Google Document AI    | Extracts medical report data automatically                |
| Gemini 1.5 Pro        | AI-powered patient history summarization                  |
| JWT Tokens            | Authentication and session management                     |
