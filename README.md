# 🚗 Claim Chatbot

The **Claim Chatbot** is a Python-based application designed to assist with generating and managing auto insurance test claims. It leverages modern frameworks like **FastAPI**, **Streamlit**, and **SQLAlchemy** to offer a seamless experience for creating, extracting, and managing claims.

---

## ✨ Features

- **Claim Synthesis**: Automatically fills in missing details for partial claims using `synthesizer.py`.
- **Information Extraction**: Extracts claim details from user input using AI-powered models (`extraction_agent.py`).
- **API Backend**: FastAPI backend with endpoints to create, retrieve, and list claims.
- **Interactive Chatbot**: Streamlit-based chatbot interface for describing incidents and generating claims.
- **Database Integration**: Stores and manages claims data using SQLite.

---

## ⚙️ Installation

Follow these steps to set up the project:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-repo/claim-chatbot.git
   cd claim-chatbot
   ```

2. **Set Up a Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up the Database**

   The SQLite database is automatically created when the FastAPI app is started.

---

## 🚀 Usage

### 1. Start the Backend API

Run the FastAPI server in the first terminal:

```bash
uvicorn app.main:app --reload
```

The API will be available at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

### 2. Set your OPENAI_API_KEY
You can set your `OPENAI_API_KEY` in one of the following ways:

#### Option 1: Set as an Environment Variable
Run the following command in your terminal:
```bash
export OPENAI_API_KEY="your-api-key-here"
```
You may also choose to set this in your `.zshrc` file for Mac, or the windows environment variable

#### Option 2: Use a `.env` File
Create a `.env` file in the project root directory and add the following line:
```
OPENAI_API_KEY=your-api-key-here
```

Make sure to install the `python-dotenv` package if not already installed:
```bash
pip install python-dotenv
```

### 2. Launch the Chatbot

Run the Streamlit chatbot interface in the second terminal:

```bash
streamlit run chatbot.py
```

The chatbot will open in your default web browser.

---

## 📁 Project Structure

```
claim-chatbot/
├── app/
│   ├── __init__.py          # App module initializer
│   ├── crud.py              # CRUD operations for claims
│   ├── database.py          # DB configuration and session management
│   ├── main.py              # FastAPI app with endpoints
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas for API validation
├── chatbot.py               # Streamlit chatbot interface
├── extraction_agent.py      # AI-powered information extraction agent
├── synthesizer.py           # Claim synthesizer logic
├── requirements.txt         # Python dependencies
├── README.md                # Project documentation
```

---

## 📡 API Endpoints

- `POST /claims/`  
  **Create a new claim**  
  **Request Body**: `ClaimCreate` schema  
  **Response**: Created claim

- `GET /claims/{claim_id}`  
  **Retrieve a claim by ID**  
  **Response**: `Claim` schema

- `GET /claims/`  
  **List all claims**  
  **Response**: List of `Claim` schemas

---

## 🔑 Key Modules

### `synthesizer.py`
- Fills in missing claim details using predefined data and randomization.
- **Example**: Generates policy numbers, adjuster names, and incident descriptions.

### `extraction_agent.py`
- Uses AI (e.g., GPT-4) to extract claim details from text.
- **Example**: Extracts vehicle info and incident context.

### `chatbot.py`
- Interactive Streamlit chatbot for incident input.
- Connects to FastAPI backend to create and manage claims.

### `app/`
- Contains FastAPI backend code, including:
  - DB models
  - Pydantic schemas
  - CRUD logic

---

## 🧩 Dependencies

The project uses the following libraries:

- **FastAPI** – Backend API framework
- **Streamlit** – Chatbot frontend
- **SQLAlchemy** – Database ORM
- **Pydantic** – Data validation
- **OpenAI** – AI-based extraction
- **Faker** – Synthetic data generation

Install all using:

```bash
pip install -r requirements.txt
```

---

## 🌱 Future Enhancements

- Integrate additional AI models for better accuracy
- Use LLM to match the POI (Point of Impact) with the incident.
- Expand database support to PostgreSQL and others
- Add advanced logging and error handling

---

## 🪪 License

This project is licensed under the **MIT License**. See the [LICENSE](./LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) – for the backend framework  
- [Streamlit](https://streamlit.io/) – for the chatbot UI  
- [OpenAI](https://openai.com/) – for AI-powered extraction  
- [Faker](https://faker.readthedocs.io/) – for synthetic data generation