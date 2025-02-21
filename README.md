# **End-to-End RAG System**  

&nbsp;

> ### **Work in Progress**  
> This is an ongoing project. Some aspects are still being refined, and certain features may be incomplete or subject to change.  

&nbsp;

## **Overview**  
This project serves as a **practical, hands-on implementation of a complete RAG system**. It demonstrates the **full retrieval and generation process**, from raw text to answers, with a **modular, reusable design**. 

This implementation manually constructs the **search pipeline**, providing a clearer view of how retrieval works at a fundamental level.  

&nbsp;
  
> You might also be interested in my work with **training BERT and GPT-2 transformers from scratch** ([repo](https://github.com/my-best-day/medium)), where I focused on model architecture, training workflows, and optimizations.  

&nbsp;


## **Goals**  
1. **Demonstrate the full RAG process**, from data ingestion to response generation  
2. **Provide a fully functional system**, including a web UI for real-world interaction and code demonstration  
3. **Use standard tools such as** Hugging Face, OpenAI, FastAPI, React + Vite, NumPy  
4. **Adhere to software and data engineering standards**  

&nbsp;

## **Engineering Details**  
- **Frontend SPA (Single Page Application) with SSR (Server Side Rendering)**, built using **React, Vite, and a UI component framework (Chakra-UI)**  
- **FastAPI backend**, serving:  
  - **SSR web UI** (Jinja2)  
  - **REST API**  
  - **CLI tools**  
- **High unit test coverage (~95%)**, using **mocking and isolation**  
- **Supports multiple datasets** with minimal code duplication  
- **DRY architecture**, enforced via **PyLint** and **Flake8**  
- **Performance optimizations**:  
  - **PyTorch batching** for similarity calculations  
  - **Efficient nearest-neighbor search** with **Polars DataFrames**  
