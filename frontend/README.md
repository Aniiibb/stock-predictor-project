Stock Prediction App
What’s Included
All source code for the backend (Django) and frontend (React)
What needs to be installed
Before you start, you need to install:
-Python 3.8 or newer
-Node.js and npm
-(Optional) NewsAPI Key
If you want live news, use my API key which i have stated below
The app will still work and show sample news if there is no key

backend(Django)
1. Open terminal/command prompt
2. install python packages
-pip install -r stock_analysis/requirements.txt
3. Set up environment variables:
-Create a file called .env in the main project folder (same place as manage.py)
-Add these 2 lines to the file 
-NEWS_API_KEY=7f6ee6bc9eb84e79b857bbdfdf4e89d8
-ALPHA_VANTAGE_API_KEY=CY3QJZLQTLGPPCP2
4. Database Migrations
-python manage.py migrate
5.Start backend
-python manage.py runserver

frontend(React)
1. Open new terminal/command prompt
- cd frontend
- npm install
- npm start

