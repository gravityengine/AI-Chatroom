# AI Chatroom

This is an open project of a chat room utilising models from [OpenAI](https://openai.com/) to generate replies. You get to choose your preferred model and ask the AI questions during conversations.

## Features

* Real-time online chatting among users
* Utilization of OpenAI GPT for intelligent response generating (supports various versions)
* Auto generation of unique usernames by the system
* Updating list of online users
* `DALL-E` Image Generation as an optional feature



## Tech Stack

* HTML/CSS/JavaScript - For frontend UI and client-side logic  
* [Flask](https://flask.palletsprojects.com/en/2.0.x/) - For backend web server 
* [Socket.IO](https://socket.io) - To enable real-time communication
* [OpenAI API](https://beta.openai.com/docs/introduction/library-reference/chapter-openai-api/reference/#python-library-v030) - To make requests to OpenAI models

Feel free to modify or extend the code according to your needs.






* pkill -f gunicorn
* nohup gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 -b 0.0.0.0:8000 app:app &
