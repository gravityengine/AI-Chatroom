# AI Chatroom

This is an open project of a chat room utilising models from [OpenAI](https://openai.com/) to generate replies. You get to choose your preferred model and ask the AI questions during conversations.

## Features

* Real-time online chatting among users
* Utilization of OpenAI GPT for intelligent response generating (supports various versions)
* Auto generation of unique usernames by the system
* Updating list of online users
* `DALL-E` Image Generation as an optional feature

<img src="chat_room_demo.jpg" alt="Chatroom Interface">

## Tech Stack

* HTML/CSS/JavaScript - For frontend UI and client-side logic  
* [Flask](https://flask.palletsprojects.com/en/2.0.x/) - For backend web server 
* [Socket.IO](https://socket.io) - To enable real-time communication
* [OpenAI API](https://beta.openai.com/docs/introduction/library-reference/chapter-openai-api/reference/#python-library-v030) - To make requests to OpenAI models

Feel free to modify or extend the code according to your needs.

## Deployment

### Environment Dependencies:
- Python 3.7 or higher needed to run the app ([Python Installation Guide](https://realpython.com/installing-python/))
- Flask (Install via ```pip install flask``` )
- python-socketio ( Install via ```pip install python-socketio``` ) 
- openai Library(Install via ```pip install openai``` )

### Steps: 

1. Clone this GitHub Repository into a local directory on your machine :
    ```
    git clone https://github.com/YOUR_GITHUB_USERNAME/AI-chat-room.git
    ```
   Replace 'YOUR_GITHUB_USERNAME' accordingly

2. Change the current directory in terminal/command prompt to that folder:

    ```
    cd AI_ChatRoom   
    ```

3. Set up your OpenAI secure key:

    ```
    export OPENAI_KEY='YOUR_OPENAI_KEY'
    ```
    Replace 'YOUR_OPENAI_KEY' with your actual secure key obtained from OpenAI
   
4. Now, launch the flask app :

    ```
    python app.py  
    ```

5. The application should now be running! Visit ```localhost:5000``` via a browser.

Please double-check if you have correctly set up the environment variable OPENAI_KEY along with verifying all the dependencies are installed successfully. Minor negligence such as overlooking messages containing crucial information might prevent successful deployment.

Once the site is up and running smoothly, feel free to host it somewhere to contribute towards the learning and development of AI.







pkill -f gunicorn
nohup gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 -b 0.0.0.0:8000 app:app &
