# Python dialogue server for Lizz
This is the ConnectedCare GitHub repository for the python dialogue server for Lizz. Using this python server, users can have back-and-forth dialogue with Lizz.

# Table of contents
- [About](about)
    - [Lizz integration](#lizz-integration)
    - [External integration](#external-integration)
- [Installation](#installation)
    - [Local with Docker](#for-local-use-with-docker)
    - [Local without Docker](#for-local-use-without-docker) 

# About
The python server comes with a `ConnectionController` class that handles the incoming and outgoing messages. It also stores data collected from Lizz or external APIs. For ease of use, a `variable.py` file is included in `app/generators` that decodes incoming information into easy to use variables such as 'USER-NAME', 'WEATHER-NOW' and 'CALENDAR-NEXT'.

## Lizz integration
The connection controller keeps track of connections with Lizz tablets. From there, incoming messages will be received and responded to using various response generators.  

Incoming and outgoing messages are encoded in JSON format. This allows us to:
- Send messages that that will be read out and displayed by Lizz
- Send options that the user can click on
- Send custom background images
- Send extra instruction routines for Lizz face and hands
- Receive messages and selected options
- Send reports on the user's mood, activities, meals, medication and sleep
- (future) Send custom actions that displays a screen on Lizz, e.g. a Youtube video

The python server can also request various information from the Lizz tablet
- User information (name, selected language, location)
- Calendar information (up to one week prior and one week in the future)
- Tablet connection status
- (future) scheduled message information
- (future) response history for reports

## External integration
The python server can also request information from external APIs to provide more engaging dialogue to the user.

### Weather API
The [Weather API](https://openweathermap.org/api) can provide current weather or future forecast weather in 3 hour intervals.

### News API
The [News API](https://newsapi.org/) can provide news based on locale and query. Other news APIs will be added in the future to be able to collect more news articles.

# Installation
## For local use with Docker
1. Place the `.env` file you were provided with into the `/app` folder.
2. Simply run ```docker compose up``` to run a local docker container.
3. You should see the message history at [localhost:2020](http://localhost:2020/)

## For local use without Docker
0. Place the `.env` file you were provided with into the `/app` folder.
1. (optional) Create a venv
2. Do ```pip install requirements.txt```
3. Run ```app.py```
4. You should see the message history at [localhost:2020](http://localhost:2020/)
