
📈 Wall Street Academy

Wall Street Academy is an interactive platform for learning and practicing stock trading using a simulated portfolio. It combines modern web technologies with blockchain integration to reward users with NFT-based achievements as they progress through their trading journey.

---

🚀 Features

- 🔐 User Authentication – Secure login and registration system  
- 📊 Portfolio Dashboard – Real-time tracking of simulated investments  
- 💹 Trading Platform – Buy and sell stocks using virtual currency  
- 🏅 Achievement NFTs – Earn blockchain-based NFTs for reaching milestones  
- 🤖 AI-Powered Assistant – Get trading tips and portfolio analysis powered by AI  
- 📊 Smart Stock Recommendations – Personalized AI-based stock suggestions using technical and behavioral data

---

🧠 AI Recommendations Engine

The recommendations system in Wall Street Academy provides personalized stock suggestions based on multiple advanced algorithms:

**How It Works**  
The system combines several techniques to tailor recommendations for each user:

- **Technical Analysis** – Evaluates indicators like RSI, MACD, and SMA  
- **Portfolio-Based Analysis** – Recommends stocks to balance existing holdings  
- **Risk Profiling** – Aligns suggestions to the user’s volatility and behavior patterns  
- **Diversification Engine** – Detects underrepresented sectors in the portfolio  
- **Collaborative Filtering** – Learns from the investment behavior of similar users  
- **Investment Goal Tracking** – Supports day traders, swing traders, and long-term investors

**Key Features**  
- Multi-factor scoring system  
- Confidence ratings for each suggestion  
- Automatic filtering of underperforming stocks  
- Contextual investment thesis with market and sector data  
- Technical indicators embedded in each recommendation

---

🛠️ Technology Stack

**Backend**
- FastAPI – High-performance web framework  
- MongoDB + Beanie – Non-relational database with async ORM  
- Web3.py – Ethereum blockchain integration  
- Hardhat – Local blockchain development environment  
- Mistral LLM – AI model for chatbot and recommendation engine  
- Ollama – Local model deployment for AI features  
- JWT – Authentication and authorization  

**Frontend**
- React – Component-based UI library  
- TailwindCSS – Utility-first styling framework  
- Chart.js – Beautiful and responsive charts  
- Axios – HTTP client for API communication  

---

⚙️ Setup Instructions

🔑 Prerequisites

Make sure you have the following installed:
- Python 3.8+  
- Node.js 14+  
- MongoDB  
- Hardhat (for blockchain features)

🧰 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/wall-street-academy.git
   cd wall-street-academy


2. Install backend dependencies
   cd backend
   pip install -r requirements.txt

3. Install frontend dependencies
   cd ../frontend
   npm install

4. Configure environment variables

   Create a .env file in backend/app/:
   BLOCKCHAIN_URL=http://localhost:8545
   PRIVATE_KEY=your_private_key
   NFT_CONTRACT_ADDRESS=your_contract_address
   MONGODB_URL=mongodb://localhost:27017
   JWT_SECRET=your_secret_key

▶️ Run the Application

Start the backend:
cd backend
python start_project.py

Start the frontend (in a new terminal):
cd frontend
npm start

---

📂 Project Structure

wall-street-academy/
├── backend/
│   ├── app/
│   │   ├── blockchain/    # Smart contracts and deployment scripts
│   │   ├── models/        # Database models
│   │   ├── routers/       # API endpoints
│   │   └── auth/          # Authentication logic
│   ├── requirements.txt   # Python dependencies
│   └── start_project.py   # Application startup script
└── frontend/
    ├── public/
    ├── src/
    │   ├── components/    # React components
    │   ├── pages/         # Page layouts
    │   ├── services/      # API integration
    │   └── utils/         # Helper functions
    └── package.json       # Node.js dependencies


---

⛓️ Blockchain Features

Wall Street Academy leverages Ethereum-compatible blockchain technology to mint NFTs that serve as achievement badges. Users can earn these for milestones such as:

- 📅 Trading for 10 consecutive days
- 💰 Reaching specific profit targets


---


📜 License

This project is licensed under the MIT License – see the LICENSE file for details.

---

👨‍💻 Contributor

Latcu Cristian Simion

---![image](https://github.com/user-attachments/assets/bbadda02-23b5-4d47-9c28-0f8a0c5745f5)![image](https://github.com/user-attachments/assets/75c79578-40b3-4e32-8656-ff417e167441)![image](https://github.com/user-attachments/assets/8adfcccb-8786-4f98-84fd-00390a56961c)![image](https://github.com/user-attachments/assets/0675c2b3-62cf-4a1b-a237-85e23b5edb8e)![image](https://github.com/user-attachments/assets/9546f4d5-b03b-4795-985b-1af0ae6f51b4)![image](https://github.com/user-attachments/assets/e42e09af-3f94-4658-bfe1-774de03d10c1)![image](https://github.com/user-attachments/assets/18a7b857-1af1-434e-8b24-55b0053047f9)![image](https://github.com/user-attachments/assets/3478e21e-5c7e-495c-a794-43b268ef6bfe)









🙏 Acknowledgements

- Financial data powered by yfinance and additional online financial datasets.
- Inspired by modern fintech platforms and blockchain-based learning models.
