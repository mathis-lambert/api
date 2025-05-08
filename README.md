# API Repository

Welcome to the `api` repository! This repository hosts the core API infrastructure for my web services, built using Python 3.13 and FastAPI. The API is designed to serve essential utilities and functionalities across all my web services, accessible under the domain `api.mathislambert.fr`.

## Projet structure

![Diagram GitDiagram](https://github.com/user-attachments/assets/eb1624c1-f0dc-4d41-98d6-01744906c195)

## 🌟 Features

- **FastAPI**: A modern, fast (high-performance) web framework for building APIs with Python 3.13 based on standard Python type hints.
- **MongoDB**: A NoSQL database used for storing application data, offering flexibility and scalability.
- **Qdrant**: A vector database used for implementing Retrieval-Augmented Generation (RAG) features, enhancing information retrieval capabilities.
- **LLM Integration**: Routes for calling the MistralAI API to leverage Large Language Models (LLMs) for various NLP tasks.
- **Versioning**: A systematic versioning approach with endpoints like `/v1`, `/v2`, etc., to manage API changes and ensure backward compatibility.

## 🚀 Getting Started

### Prerequisites

- Python 3.13
- MongoDB instance
- Qdrant instance
- MistralAI API key

### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/api.git self_api
   cd self_api
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the root directory and add the following variables:
   ```
   MONGODB_URI=your_mongodb_connection_string
   QDRANT_URI=your_qdrant_connection_string
   MISTRAL_API_KEY=your_mistral_api_key
   ```

### Running the API

Start the FastAPI server using:
```bash
uvicorn main:app --host 0.0.0.0 --port 3001 --reload
```

The API will be accessible at `http://127.0.0.1:3001`.

## 🛣️ API Endpoints

### Versioning

- **Base URL**: `https://api.mathislambert.fr`
- **Versioning Structure**: `/v1`, `/v2`, etc.

### Example Endpoints

- **Health Check**:
  - `GET /v1/health`: Check the status of the API.

- **LLM Routes**:
  - `POST /v1/chat/completions`: Generate text completions using the MistralAI API.

- **Data Routes**:
  - `GET /v1/data`: Retrieve data from MongoDB.
  - `POST /v1/data`: Insert data into MongoDB.

- **RAG Features**:
  - `POST /v1/rag/query`: Query the Qdrant database for enhanced information retrieval using RAG.

## 🤝 Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request. Let's build something amazing together!

## 📜 License

This project is licensed under the MIT License. Feel free to explore, modify, and share!

## 📞 Contact

Have questions or want to chat? Feel free to reach out!

- [LinkedIn](https://www.linkedin.com/in/mathis-lambert) 🔗

---

Happy coding! 💻✨

