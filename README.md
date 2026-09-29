# 🏥 MediTrack – AI-Powered Clinical Decision Support System

MediTrack is an **AI-powered clinical decision support system** designed to assist doctors with patient data management, medical knowledge retrieval, drug information, and X-ray pre-screening.

The platform combines **Retrieval-Augmented Generation (RAG)**, **Large Language Models (LLMs)**, **YOLOv8**, **Google Document AI**, and **Model Context Protocol (MCP)** to provide grounded clinical assistance through a microservice-based architecture.

> ⚠️ **Disclaimer:** MediTrack is a research prototype developed to support healthcare professionals. It is not intended to replace professional medical diagnosis, clinical judgment, or treatment decisions.

---

### Key Features

- **Symptom-Based Clinical RAG** for grounded medical Q&A on diseases, symptoms, diagnosis, and treatment.
- **Agentic Drug-Information RAG** for medication uses, side effects, safety, substitutes, and patient-specific considerations.
- **Fine-Tuned YOLOv8 X-ray Pre-Screening** for detecting and highlighting potential fracture regions.
- **Google Document AI Integration** for automated extraction of structured data from laboratory reports.
- **AI-Powered Patient Summaries** combining recent lab results, medications, and doctor notes.
- **MCP-Based AI Orchestration** using LangGraph to intelligently route requests across specialized clinical services.
- **Consultation Context Management** to maintain patient-specific conversational context during an active consultation.
- **Doctor-Focused Interface** for accessing patient records, AI assistance, medical reports, and X-ray analysis.

---

### System Architecture

![MediTrack System Architecture](meditrack-dark.svg)

MediTrack follows a **microservice-based architecture** with a LangGraph-powered orchestrator coordinating specialized AI services through the **Model Context Protocol (MCP)**.

Based on the doctor's request, the orchestrator routes the query to the appropriate **Disease & Symptom RAG**, **Drug RAG**, **X-ray Analysis**, or **Patient Data** service.

---

### Core Services

#### 🩺 Disease & Symptom RAG

Provides grounded responses to clinical questions related to diseases, symptoms, diagnosis, and treatment by retrieving relevant information from the medical knowledge base.

**Technologies:** Spring Boot, Spring AI, PGVector, Ollama Embeddings, Cerebras

#### 💊 Drug-Information RAG

Processes medication-related questions and retrieves relevant information about drug uses, side effects, safety considerations, substitutes, and other available drug information.

**Technologies:** Spring Boot, Spring AI, PGVector, Gemini Embeddings, Groq

#### 🩻 X-ray Pre-Screening

Uses a fine-tuned **YOLOv8** model to analyze uploaded X-ray images, detect potential fracture regions, and return the detected regions with confidence information.

**Technologies:** Python, FastAPI, YOLOv8, OpenCV, Groq

#### 📄 Medical Document Processing

Uses **Google Document AI** to extract structured information such as test names, values, units, and reference ranges from uploaded laboratory reports.

**Technologies:** Spring Boot, Google Document AI, MongoDB

#### 🧠 Patient Summarization

Combines recent laboratory results, prescribed medications, and doctor notes to generate a concise overview of the patient's available medical information.

**Technologies:** Spring Boot, LLM, MongoDB

#### 🔗 MCP Orchestration

Uses **LangGraph** and **Model Context Protocol (MCP)** to connect and coordinate the specialized clinical services. The orchestrator determines which service should handle each doctor's request.

**Technologies:** Python, FastAPI, LangGraph, LangChain, MCP

---

### Technology Stack

| Category | Technologies |
|---|---|
| **Frontend** | React |
| **Backend** | Java, Spring Boot |
| **AI / RAG** | Spring AI, LangChain, LangGraph |
| **LLMs** | Cerebras, Groq |
| **Embeddings** | Ollama, Gemini |
| **Vector Database** | PostgreSQL, PGVector |
| **Medical Imaging** | YOLOv8, OpenCV |
| **Document Processing** | Google Document AI |
| **Databases** | MySQL, MongoDB, PostgreSQL |
| **AI Orchestration** | Model Context Protocol (MCP), LangGraph |
| **API Development** | Spring REST, FastAPI |
| **Deployment** | Docker, Docker Compose |

---

### Project Structure

```text
MediTrack/
│
├── Backend/
│   └── Patient data, medical reports, notes and summaries
│
├── RAG/
│   └── Disease and symptom RAG service
│
├── Drug-RAG-Service/
│   └── Drug-information RAG service
│
├── Xray-Service/
│   └── YOLOv8 X-ray pre-screening service
│
├── MediTrack-Orchestrator/
│   └── LangGraph and MCP orchestration
│
├── frontend/
│   └── React doctor interface
│
├── meditrack-dark.svg
│   └── System architecture diagram
│
├── Workflow.svg
│   └── MediTrack workflow diagram
│
└── docker-compose.yml
```

---

### Service Overview

| Service | Purpose | Port |
|---|---|---:|
| **Frontend** | Doctor-facing user interface | 3000 |
| **Backend** | Patient and medical data management | 8080 |
| **Disease RAG** | Disease and symptom assistance | 8081 |
| **Drug RAG** | Drug-information assistance | 8082 |
| **X-ray Service** | X-ray fracture pre-screening | 8083 |
| **MCP Orchestrator** | AI service routing and orchestration | 8094 |

---

### System Workflow

![MediTrack System Workflow](Workflow.svg)

The doctor interacts with MediTrack through a unified interface. The **MCP orchestrator** interprets each request and routes it to the appropriate specialized service. The selected service processes the request and returns the result to the doctor through the same consultation interface.

---

### Limitations

- **X-ray Input Quality** – The model performs best on clinical X-ray images similar to those used during training and may be less reliable on photographed, edited, stock, or colorized images.
- **Knowledge-Source Dependency** – RAG responses are limited by the information available in the underlying medical and drug datasets.
- **External AI Services** – Some functionality depends on external LLM APIs and their availability or rate limits.
- **Research Prototype** – MediTrack has not undergone clinical validation and should not be used as an autonomous diagnostic system.

---

### Future Work

- **Larger X-ray Dataset** – Train the detection model using more diverse medical images to improve robustness and detection performance.
- **Extended Medical Imaging** – Expand AI pre-screening capabilities to other imaging modalities such as **CT and MRI**.
- **Expanded Medical Knowledge** – Integrate additional validated medical knowledge sources for broader clinical information retrieval.

---
