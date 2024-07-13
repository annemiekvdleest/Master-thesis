# Python dialogue server for Lizz
This is the GitHub repository for the python dialogue server for Lizz. 

# Table of contents
- [About](about)
    - [Lizz integration](#lizz-integration)
    - [External integration](#external-integration)

# About
The python server comes with a `ConnectionController` class that handles the incoming and outgoing messages. It also stores data collected from Lizz or external APIs. For ease of use, a `variable.py` file is included in `app/generators` that decodes incoming information into easy to use variables such as 'USER-NAME', 'WEATHER-NOW' and 'CALENDAR-NEXT'.

## Lizz integration
The connection controller keeps track of connections with Lizz tablets. From there, incoming messages will be received and responded to using various response generators.  

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

