import locale
from enum import Enum
from datetime import datetime, timedelta
import pandas as pd
import glob
import re
import inflect
from dateutil import tz as dt_tz

file_list = glob.glob("config/variables/**/*.tsv", recursive=True)
variables_df = pd.concat([pd.read_csv(filename, sep="\t", index_col=None) for filename in file_list], axis=0,
                         ignore_index=True)

inf_eng = inflect.engine()

MISSING_VAL = "??MISSING??"

# TODO: move these values to variables files
defaults = {"CLIENT-NAME": "client",  # the name of the user
            "DIALOGUE-MORE-OPTIONS": "more-options",  # more options
            "ASSISTANT-NAME": "assistant-name",  # the name of the tablet
            "DATETIME-NOW-DAYPART": "daypart",  # the time of day (morning, afternoon, evening, night)
            "DATETIME-NOW-TIME": "now",  # the time of day in (in 24)hours:minutes
            "DATETIME-NOW-HOUR": MISSING_VAL,  # the current hour of the day (in 12)
            "DATETIME-NOW-MINUTE": MISSING_VAL,  # the current minute of the day
            "DATETIME-NOW-SECOND": MISSING_VAL,  # the current second of the day
            "DATETIME-TODAY-DAY": MISSING_VAL,  # the day today in number of the month (1, 2, 3 etc)
            "DATETIME-TODAY-DAY-ORDINAL": MISSING_VAL,  # the day today in ordinal number of the month (1st, 2nd, 3rd etc)
            "DATETIME-TODAY-WEEKDAY": MISSING_VAL,  # the day today in language (monday, tuesday, wednesday, etc.)
            "DATETIME-TODAY-MONTH": MISSING_VAL,  # the month today in language (january, february, etc.)
            "DATETIME-TODAY-YEAR": MISSING_VAL,  # the year today in numbers (e.g. 2023)
            "DATETIME-TOMORROW-DAY": MISSING_VAL,  # the day tomorrow in number of the month
            "DATETIME-TOMORROW-DAY-ORDINAL": MISSING_VAL,  # the day tomorrow in ordinal number of the month (1st, 2nd, 3rd etc)
            "DATETIME-TOMORROW-WEEKDAY": MISSING_VAL,  # the day tomorrow in language (monday, tuesday, wednesday, etc.)
            "DATETIME-TOMORROW-MONTH": MISSING_VAL,  # the month tomorrow in language (january, february, etc.)
            "DATETIME-TOMORROW-YEAR": MISSING_VAL,  # the year tomorrow in numbers (e.g. 2023)
            "DATETIME-YESTERDAY-DAY": MISSING_VAL,  # the day yesterday in number of the month (1, 2, 3 etc)
            "DATETIME-YESTERDAY-DAY-ORDINAL": MISSING_VAL,  # the day yesterday in ordinal number of the month (1st, 2nd, 3rd etc)
            "DATETIME-YESTERDAY-WEEKDAY": MISSING_VAL,  # the day yesterday in language (monday, tuesday, wednesday, etc.)
            "DATETIME-YESTERDAY-MONTH": MISSING_VAL,  # the month yesterday in language (january, february, etc.)
            "DATETIME-YESTERDAY-YEAR": MISSING_VAL,  # the year yesterday in numbers (e.g. 2023)
            "CLIENT-LOCATION-CITY": "somewhere",  # the city that the tablet is located in
            "CLIENT-LOCATION-COUNTRY": "somewhere",  # the country that the tablet is located in
            "CALENDAR-NOW": "nothing",  # the current calendar appointment
            "CALENDAR-NOW-TIME": "right-now",  # time of current calendar appointment in "at hour:minute"
            "CALENDAR-NEXT-TODAY": "nothing",  # the next appointment of the day
            "CALENDAR-NEXT-TODAY-TIME": "rest-of-day",  # time of next appointment of the day in "until hour:minute"
            "CALENDAR-NEXT": "nothing",  # the next appointment in the calendar
            "CALENDAR-NEXT-TIME": "next",  # time of next appointment in the calendar in "at hour:minute"
            "CALENDAR-NEXT-TOMORROW": "nothing",  # the next appointment of tomorrow
            "CALENDAR-NEXT-TOMORROW-TIME": "tomorrow",  # time of next appointment of tomorrow in "tomorrow at hour:minute"
            "CALENDAR-LAST": "nothing",  # the previous appointment in the calendar
            "CALENDAR-LAST-TIME": "before",  # time of previous appointment in the calendar in "at hour:minute"
            "CALENDAR-LAST-YESTERDAY": "nothing",  # the last appointment of yesterday
            "CALENDAR-LAST-YESTERDAY-TIME": "yesterday",  # time of last appointment of yesterday in "yesterday at hour:minute"
            "CALENDAR-LAST-TOMORROW": "nothing",  # the last appointment of tomorrow
            "CALENDAR-LAST-TOMORROW-TIME": "tomorrow",  # time of last appointment of tomorrow in "tomorrow at hour:minute"
            "CALENDAR-LAST-TODAY": "nothing",  # the last appointment of today
            "CALENDAR-LAST-TODAY-TIME": "today",  # time of last appointment of today in "at hour:minute"
            "WEATHER-NOW": MISSING_VAL,  # current weather conditions
            "WEATHER-NOW-TEMP": MISSING_VAL,  # current measured temperature outside (in celcius)
            "WEATHER-NOW-TEMP-FEEL": MISSING_VAL,  # current feel temperature outside (in celcius)
            "WEATHER-NOW-TEMP-MIN": MISSING_VAL,  # current minimum observed temperature outside (in celcius)
            "WEATHER-NOW-TEMP-MAX": MISSING_VAL,  # current maximum observed temperature outside (in celcius)
            "WEATHER-NOW-PRESSURE": MISSING_VAL,  # current atmospheric pressure outside on sea level (in hPa)
            "WEATHER-NOW-HUMIDITY": MISSING_VAL,  # current humidity outside (in percent)
            "WEATHER-NOW-WIND-SPEED": MISSING_VAL,  # current speed of the wind outside (in meters per second)
            "WEATHER-NOW-WIND-DIRECTION": MISSING_VAL,  # current direction of the wind outside (in degrees)
            "WEATHER-NOW-VISIBILITY": MISSING_VAL,  # current visibility outside (in meters, max is 10000m)
            "WEATHER-NOW-CLOUDS": MISSING_VAL,  # current cloudiness in the sky (in percent; 100% means fully clouded)
            "WEATHER-NOW-RAIN": MISSING_VAL,  # millimeters of rainfall in the last hour
            "WEATHER-NOW-SNOW": MISSING_VAL,  # millimeters of snowfall in the last hour
            "WEATHER-FORECAST-NEXT-HOUR": MISSING_VAL,  # weather conditions in the next hour
            "WEATHER-FORECAST-NEXT-HOUR-TEMP": MISSING_VAL,  # measured temperature outside (in celcius) in the next hour
            "WEATHER-FORECAST-NEXT-HOUR-TEMP-FEEL": MISSING_VAL,  # feel temperature outside (in celcius) in the next hour
            "WEATHER-FORECAST-NEXT-HOUR-TEMP-MIN": MISSING_VAL,  # minimum observed temperature outside (in celcius) in the next hour
            "WEATHER-FORECAST-NEXT-HOUR-TEMP-MAX": MISSING_VAL,  # maximum observed temperature outside (in celcius) in the next hour
            "WEATHER-FORECAST-NEXT-HOUR-PRESSURE": MISSING_VAL,  # atmospheric pressure outside on sea level (in hPa) in the next hour
            "WEATHER-FORECAST-NEXT-HOUR-HUMIDITY": MISSING_VAL,  # humidity outside (in percent) in the next hour
            "WEATHER-FORECAST-NEXT-HOUR-WIND-SPEED": MISSING_VAL,  # speed of the wind outside (in meters per second) in the next hour
            "WEATHER-FORECAST-NEXT-HOUR-WIND-DIRECTION": MISSING_VAL,  # direction of the wind outside (in degrees) in the next hour
            "WEATHER-FORECAST-NEXT-HOUR-VISIBILITY": MISSING_VAL,  # visibility outside (in meters, max is 10000m) in the next hour
            "WEATHER-FORECAST-NEXT-HOUR-CLOUDS": MISSING_VAL,  # cloudiness in the sky (in percent; 100% means fully clouded) in the next hour
            "WEATHER-FORECAST-NEXT-HOUR-RAIN": MISSING_VAL,  # millimeters of rainfall in the next hour
            "WEATHER-FORECAST-NEXT-HOUR-SNOW": MISSING_VAL,  # millimeters of snowfall in the next hour
            "WEATHER-FORECAST-AFTER-NEXT-HOUR": MISSING_VAL,  # weather conditions after next hour
            "WEATHER-FORECAST-AFTER-NEXT-HOUR-TEMP": MISSING_VAL,  # measured temperature outside (in celcius) after next hour
            "WEATHER-FORECAST-AFTER-NEXT-HOUR-TEMP-FEEL": MISSING_VAL,  # feel temperature outside (in celcius) after next hour
            "WEATHER-FORECAST-AFTER-NEXT-HOUR-TEMP-MIN": MISSING_VAL,  # minimum observed temperature outside (in celcius) after next hour
            "WEATHER-FORECAST-AFTER-NEXT-HOUR-TEMP-MAX": MISSING_VAL,  # maximum observed temperature outside (in celcius) after next hour
            "WEATHER-FORECAST-AFTER-NEXT-HOUR-PRESSURE": MISSING_VAL,  # atmospheric pressure outside on sea level (in hPa) after next hour
            "WEATHER-FORECAST-AFTER-NEXT-HOUR-HUMIDITY": MISSING_VAL,  # humidity outside (in percent) after next hour
            "WEATHER-FORECAST-AFTER-NEXT-HOUR-WIND-SPEED": MISSING_VAL,  # speed of the wind outside (in meters per second) after next hour
            "WEATHER-FORECAST-AFTER-NEXT-HOUR-WIND-DIRECTION": MISSING_VAL,  # direction of the wind outside (in degrees) after next hour
            "WEATHER-FORECAST-AFTER-NEXT-HOUR-VISIBILITY": MISSING_VAL,  # visibility outside (in meters, max is 10000m) after next hour
            "WEATHER-FORECAST-AFTER-NEXT-HOUR-CLOUDS": MISSING_VAL,  # cloudiness in the sky (in percent; 100% means fully clouded) after next hour
            "WEATHER-FORECAST-AFTER-NEXT-HOUR-RAIN": MISSING_VAL,  # millimeters of rainfall after next hour
            "WEATHER-FORECAST-AFTER-NEXT-HOUR-SNOW": MISSING_VAL,  # millimeters of snowfall after next hour
            "WEATHER-FORECAST-THIS-MORNING": MISSING_VAL,  # forecasted weather conditions this morning
            "WEATHER-FORECAST-THIS-MORNING-TEMP": MISSING_VAL,  # forecasted measured temperature this morning (in celcius)
            "WEATHER-FORECAST-THIS-MORNING-TEMP-FEEL": MISSING_VAL,  # forecasted feel temperature this morning (in celcius)
            "WEATHER-FORECAST-THIS-MORNING-TEMP-MIN": MISSING_VAL,  # forecasted minimum observed temperature this morning (in celcius)
            "WEATHER-FORECAST-THIS-MORNING-TEMP-MAX": MISSING_VAL,   # forecasted maximum observed temperature this morning (in celcius)
            "WEATHER-FORECAST-THIS-MORNING-PRESSURE": MISSING_VAL,  # forecasted atmospheric pressure this morning on sea level (in hPa)
            "WEATHER-FORECAST-THIS-MORNING-HUMIDITY": MISSING_VAL,  # forecasted humidity this morning (in percent)
            "WEATHER-FORECAST-THIS-MORNING-WIND-SPEED": MISSING_VAL,  # forecasted speed of the wind this morning (in meters per second)
            "WEATHER-FORECAST-THIS-MORNING-WIND-DIRECTION": MISSING_VAL,  # forecasted direction of the wind this morning (in degrees)
            "WEATHER-FORECAST-THIS-MORNING-VISIBILITY": MISSING_VAL,  # forecasted visibility this morning (in meters, max is 10000m)
            "WEATHER-FORECAST-THIS-MORNING-CLOUDS": MISSING_VAL,  # forecasted cloudiness this morning (in percent; 100% means fully clouded)
            "WEATHER-FORECAST-THIS-MORNING-RAIN": MISSING_VAL,  # forecasted millimeters of rainfall this morning
            "WEATHER-FORECAST-THIS-MORNING-SNOW": MISSING_VAL,  # forecasted millimeters of snowfall this morning
            "WEATHER-FORECAST-THIS-AFTERNOON": MISSING_VAL,  # forecasted weather conditions this afternoon
            "WEATHER-FORECAST-THIS-AFTERNOON-TEMP": MISSING_VAL,  # forecasted measured temperature this afternoon (in celcius)
            "WEATHER-FORECAST-THIS-AFTERNOON-TEMP-FEEL": MISSING_VAL,  # forecasted feel temperature this afternoon (in celcius)
            "WEATHER-FORECAST-THIS-AFTERNOON-TEMP-MIN": MISSING_VAL,  # forecasted minimum observed temperature this afternoon (in celcius)
            "WEATHER-FORECAST-THIS-AFTERNOON-TEMP-MAX": MISSING_VAL,  # forecasted maximum observed temperature this afternoon (in celcius)
            "WEATHER-FORECAST-THIS-AFTERNOON-PRESSURE": MISSING_VAL,  # forecasted atmospheric pressure this afternoon on sea level (in hPa)
            "WEATHER-FORECAST-THIS-AFTERNOON-HUMIDITY": MISSING_VAL,  # forecasted humidity this afternoon (in percent)
            "WEATHER-FORECAST-THIS-AFTERNOON-WIND-SPEED": MISSING_VAL,  # forecasted speed of the wind this afternoon (in meters per second)
            "WEATHER-FORECAST-THIS-AFTERNOON-WIND-DIRECTION": MISSING_VAL, # forecasted direction of the wind this afternoon (in degrees)
            "WEATHER-FORECAST-THIS-AFTERNOON-VISIBILITY": MISSING_VAL, # forecasted visibility this afternoon (in meters, max is 10000m)
            "WEATHER-FORECAST-THIS-AFTERNOON-CLOUDS": MISSING_VAL,  # forecasted cloudiness this afternoon (in percent; 100% means fully clouded)
            "WEATHER-FORECAST-THIS-AFTERNOON-RAIN": MISSING_VAL,  # forecasted millimeters of rainfall this afternoon
            "WEATHER-FORECAST-THIS-AFTERNOON-SNOW": MISSING_VAL,  # forecasted millimeters of snowfall this afternoon
            "WEATHER-FORECAST-THIS-EVENING": MISSING_VAL,  # forecasted weather conditions this evening
            "WEATHER-FORECAST-THIS-EVENING-TEMP": MISSING_VAL,  # forecasted measured temperature this evening (in celcius)
            "WEATHER-FORECAST-THIS-EVENING-TEMP-FEEL": MISSING_VAL,  # forecasted feel temperature this evening (in celcius)
            "WEATHER-FORECAST-THIS-EVENING-TEMP-MIN": MISSING_VAL,  # forecasted minimum observed temperature this evening (in celcius)
            "WEATHER-FORECAST-THIS-EVENING-TEMP-MAX": MISSING_VAL,  # forecasted maximum observed temperature this evening (in celcius)
            "WEATHER-FORECAST-THIS-EVENING-PRESSURE": MISSING_VAL,  # forecasted atmospheric pressure this evening on sea level (in hPa)
            "WEATHER-FORECAST-THIS-EVENING-HUMIDITY": MISSING_VAL,  # forecasted humidity this evening (in percent)
            "WEATHER-FORECAST-THIS-EVENING-WIND-SPEED": MISSING_VAL,  # forecasted speed of the wind this evening (in meters per second)
            "WEATHER-FORECAST-THIS-EVENING-WIND-DIRECTION": MISSING_VAL,  # forecasted direction of the wind this evening (in degrees)
            "WEATHER-FORECAST-THIS-EVENING-VISIBILITY": MISSING_VAL,  # forecasted visibility this evening (in meters, max is 10000m)
            "WEATHER-FORECAST-THIS-EVENING-CLOUDS": MISSING_VAL,  # forecasted cloudiness this evening (in percent; 100% means fully clouded)
            "WEATHER-FORECAST-THIS-EVENING-RAIN": MISSING_VAL,  # forecasted millimeters of rainfall this evening
            "WEATHER-FORECAST-THIS-EVENING-SNOW": MISSING_VAL,  # forecasted millimeters of snowfall this evening
            "WEATHER-FORECAST-TOMORROW": MISSING_VAL,  # forecasted weather conditions tomorow
            "WEATHER-FORECAST-TOMORROW-TEMP": MISSING_VAL,  # forecasted temperature tomorrow (in celcius)
            "WEATHER-FORECAST-TOMORROW-TEMP-FEEL": MISSING_VAL,  # forecasted feel temperature tomorrow (in celcius)
            "WEATHER-FORECAST-TOMORROW-TEMP-MIN": MISSING_VAL,  # forecasted minimum observed temperature tomorrow (in celcius)
            "WEATHER-FORECAST-TOMORROW-TEMP-MAX": MISSING_VAL,  # forecasted maximum observed temperature tomorrow (in celcius)
            "WEATHER-FORECAST-TOMORROW-PRESSURE": MISSING_VAL,  # forecasted atmospheric pressure tomorrow on sea level (in hPa)
            "WEATHER-FORECAST-TOMORROW-HUMIDITY": MISSING_VAL,  # forecasted humidity tomorrow (in percent)
            "WEATHER-FORECAST-TOMORROW-WIND-SPEED": MISSING_VAL,  # forecasted speed of the wind tomorrow (in meters per second)
            "WEATHER-FORECAST-TOMORROW-WIND-DIRECTION": MISSING_VAL,  # forecasted direction of the wind tomorrow (in degrees)
            "WEATHER-FORECAST-TOMORROW-VISIBILITY": MISSING_VAL,  # forecasted visibility tomorrow (in meters, max is 10000m)
            "WEATHER-FORECAST-TOMORROW-CLOUDS": MISSING_VAL,  # forecasted cloudiness tomorrow (in percent; 100% means fully clouded)
            "WEATHER-FORECAST-TOMORROW-RAIN": MISSING_VAL,  # forecasted millimeters of rainfall tomorrow
            "WEATHER-FORECAST-TOMORROW-SNOW": MISSING_VAL,  # forecasted millimeters of snowfall tomorrow
            "WEATHER-FORECAST-TOMORROW-MORNING": MISSING_VAL,  # forecasted weather conditions tomorrow morning
            "WEATHER-FORECAST-TOMORROW-MORNING-TEMP": MISSING_VAL,  # forecasted measured temperature tomorrow morning (in celcius)
            "WEATHER-FORECAST-TOMORROW-MORNING-TEMP-FEEL": MISSING_VAL,  # forecasted feel temperature tomorrow morning (in celcius)
            "WEATHER-FORECAST-TOMORROW-MORNING-TEMP-MIN": MISSING_VAL,  # forecasted minimum observed temperature tomorrow morning (in celcius)
            "WEATHER-FORECAST-TOMORROW-MORNING-TEMP-MAX": MISSING_VAL,  # forecasted maximum observed temperature tomorrow morning (in celcius)
            "WEATHER-FORECAST-TOMORROW-MORNING-PRESSURE": MISSING_VAL,  # forecasted atmospheric pressure tomorrow morning on sea level (in hPa)
            "WEATHER-FORECAST-TOMORROW-MORNING-HUMIDITY": MISSING_VAL,  # forecasted humidity tomorrow morning (in percent)
            "WEATHER-FORECAST-TOMORROW-MORNING-WIND-SPEED": MISSING_VAL,  # forecasted speed of the wind tomorrow morning (in meters per second)
            "WEATHER-FORECAST-TOMORROW-MORNING-WIND-DIRECTION": MISSING_VAL,  # forecasted direction of the wind tomorrow morning (in degrees)
            "WEATHER-FORECAST-TOMORROW-MORNING-VISIBILITY": MISSING_VAL, # forecasted visibility tomorrow morning (in meters, max is 10000m)
            "WEATHER-FORECAST-TOMORROW-MORNING-CLOUDS": MISSING_VAL,  # forecasted cloudiness tomorrow morning (in percent; 100% means fully clouded)
            "WEATHER-FORECAST-TOMORROW-MORNING-RAIN": MISSING_VAL,  # forecasted millimeters of rainfall tomorrow morning
            "WEATHER-FORECAST-TOMORROW-MORNING-SNOW": MISSING_VAL,  # forecasted millimeters of snowfall tomorrow morning
            "WEATHER-FORECAST-TOMORROW-AFTERNOON": MISSING_VAL,  # forecasted weather conditions tomorrow afternoon
            "WEATHER-FORECAST-TOMORROW-AFTERNOON-TEMP": MISSING_VAL,  # forecasted measured temperature tomorrow afternoon (in celcius)
            "WEATHER-FORECAST-TOMORROW-AFTERNOON-TEMP-FEEL": MISSING_VAL,  # forecasted feel temperature tomorrow afternoon (in celcius)
            "WEATHER-FORECAST-TOMORROW-AFTERNOON-TEMP-MIN": MISSING_VAL,  # forecasted minimum observed temperature tomorrow afternoon (in celcius)
            "WEATHER-FORECAST-TOMORROW-AFTERNOON-TEMP-MAX": MISSING_VAL,  # forecasted maximum observed temperature tomorrow afternoon (in celcius)
            "WEATHER-FORECAST-TOMORROW-AFTERNOON-PRESSURE": MISSING_VAL,  # forecasted atmospheric pressure tomorrow afternoon on sea level (in hPa)
            "WEATHER-FORECAST-TOMORROW-AFTERNOON-HUMIDITY": MISSING_VAL,  # forecasted humidity tomorrow afternoon (in percent)
            "WEATHER-FORECAST-TOMORROW-AFTERNOON-WIND-SPEED": MISSING_VAL,  # forecasted speed of the wind tomorrow afternoon (in meters per second)
            "WEATHER-FORECAST-TOMORROW-AFTERNOON-WIND-DIRECTION": MISSING_VAL,  # forecasted direction of the wind tomorrow afternoon (in degrees)
            "WEATHER-FORECAST-TOMORROW-AFTERNOON-VISIBILITY": MISSING_VAL,  # forecasted visibility tomorrow afternoon (in meters, max is 10000m)
            "WEATHER-FORECAST-TOMORROW-AFTERNOON-CLOUDS": MISSING_VAL,  # forecasted cloudiness tomorrow afternoon (in percent; 100% means fully clouded)
            "WEATHER-FORECAST-TOMORROW-AFTERNOON-RAIN": MISSING_VAL,  # forecasted millimeters of rainfall tomorrow afternoon
            "WEATHER-FORECAST-TOMORROW-AFTERNOON-SNOW": MISSING_VAL,  # forecasted millimeters of snowfall tomorrow afternoon
            "WEATHER-FORECAST-TOMORROW-EVENING": MISSING_VAL,  # forecasted weather conditions tomorrow evening
            "WEATHER-FORECAST-TOMORROW-EVENING-TEMP": MISSING_VAL,  # forecasted measured temperature tomorrow evening (in celcius)
            "WEATHER-FORECAST-TOMORROW-EVENING-TEMP-FEEL": MISSING_VAL,  # forecasted feel temperature tomorrow evening (in celcius)
            "WEATHER-FORECAST-TOMORROW-EVENING-TEMP-MIN": MISSING_VAL,  # forecasted minimum observed temperature tomorrow evening (in celcius)
            "WEATHER-FORECAST-TOMORROW-EVENING-TEMP-MAX": MISSING_VAL,  # forecasted maximum observed temperature tomorrow evening (in celcius)
            "WEATHER-FORECAST-TOMORROW-EVENING-PRESSURE": MISSING_VAL,  # forecasted atmospheric pressure tomorrow evening on sea level (in hPa)
            "WEATHER-FORECAST-TOMORROW-EVENING-HUMIDITY": MISSING_VAL,  # forecasted humidity tomorrow evening (in percent)
            "WEATHER-FORECAST-TOMORROW-EVENING-WIND-SPEED": MISSING_VAL,  # forecasted speed of the wind tomorrow evening (in meters per second)
            "WEATHER-FORECAST-TOMORROW-EVENING-WIND-DIRECTION": MISSING_VAL,  # forecasted direction of the wind tomorrow evening (in degrees)
            "WEATHER-FORECAST-TOMORROW-EVENING-VISIBILITY": MISSING_VAL,  # forecasted visibility tomorrow evening (in meters, max is 10000m)
            "WEATHER-FORECAST-TOMORROW-EVENING-CLOUDS": MISSING_VAL,  # forecasted cloudiness tomorrow evening (in percent; 100% means fully clouded)
            "WEATHER-FORECAST-TOMORROW-EVENING-RAIN": MISSING_VAL,  # forecasted millimeters of rainfall tomorrow evening
            "WEATHER-FORECAST-TOMORROW-EVENING-SNOW": MISSING_VAL,  # forecasted millimeters of snowfall tomorrow evening
            "NEWS-TODAY-TITLE": MISSING_VAL,   # The latest news article title from today
            "NEWS-TODAY-AUTHOR": MISSING_VAL,  # The latest news article from today author
            "NEWS-TODAY-PUBLISHED-AT": MISSING_VAL,  # The latest news article from today publish time in "at hour:minute"
            "NEWS-TODAY-SOURCE": MISSING_VAL,  # The latest news article from today source (e.g. Google)
            "NEWS-LATEST-TITLE": MISSING_VAL,  # The latest news article title
            "NEWS-LATEST-AUTHOR": MISSING_VAL,  # The latest news article author
            "NEWS-LATEST-PUBLISHED-AT": MISSING_VAL,  # The latest news article publish time in "at hour:minute"
            "NEWS-LATEST-SOURCE": MISSING_VAL,  # The latest news article source (e.g. Google)
            "REPORT-LAST-MEDICATION-VALUE": MISSING_VAL,  # The answer of the latest medicine report by the user
            "REPORT-LAST-MEDICATION-TIME": MISSING_VAL, # The time of the latest medicine report by the user
            "REPORT-LAST-SLEEP-VALUE": MISSING_VAL,  # The answer of the latest sleep report by the user
            "REPORT-LAST-SLEEP-TIME": MISSING_VAL,  # The time of the latest sleep report by the user
            "REPORT-LAST-MEAL-VALUE": MISSING_VAL,  # The answer of the latest meal report by the user
            "REPORT-LAST-MEAL-TIME": MISSING_VAL,  # The time of the latest meal report by the user
            "REPORT-LAST-ACTIVITY-VALUE": MISSING_VAL,  # The answer of the latest activity report by the user
            "REPORT-LAST-ACTIVITY-TIME": MISSING_VAL,  # The time of the latest activity report by the user
            "REPORT-LAST-MOOD-VALUE": MISSING_VAL,  # The answer of the latest mood report by the user
            "REPORT-LAST-MOOD-TIME": MISSING_VAL,  # The time of the latest mood report by the user
            }
capitalize = {"CLIENT-NAME",
              "ASSISTANT-NAME",
              "CLIENT-LOCATION-CITY",
              "CLIENT-LOCATION-COUNTRY",
              "DATETIME-TODAY-MONTH",
              "DATETIME-TOMORROW-MONTH",
              "DATETIME-YESTERDAY-MONTH",
              }

class Defaults(str, Enum):

    def __new__(cls, value):
        member = str.__new__(cls, value)
        member._value_ = value
        member.default_value = defaults[value] if value in defaults else MISSING_VAL
        member.capitalized = value in capitalize
        return member

    CLIENT_NAME = "CLIENT-NAME"
    ASSISTANT_NAME = "ASSISTANT-NAME"

    CLIENT_LOCATION_CITY = "CLIENT-LOCATION-CITY"
    CLIENT_LOCATION_COUNTRY = "CLIENT-LOCATION-COUNTRY"

    DIALOGUE_MORE_OPTIONS = "DIALOGUE-MORE-OPTIONS"

    DATETIME_NOW_DAYPART = "DATETIME-NOW-DAYPART"
    DATETIME_NOW_TIME = "DATETIME-NOW-TIME"
    DATETIME_NOW_HOUR = "DATETIME-NOW-HOUR"
    DATETIME_NOW_MINUTE = "DATETIME-NOW-MINUTE"
    DATETIME_NOW_SECOND = "DATETIME-NOW-SECOND"
    DATETIME_TODAY_DAY = "DATETIME-TODAY-DAY"
    DATETIME_TODAY_DAY_ORDINAL = "DATETIME-TODAY-DAY-ORDINAL"
    DATETIME_TODAY_WEEKDAY = "DATETIME-TODAY-WEEKDAY"
    DATETIME_TODAY_MONTH = "DATETIME-TODAY-MONTH"
    DATETIME_TODAY_YEAR = "DATETIME-TODAY-YEAR"
    DATETIME_TOMORROW_DAY = "DATETIME-TOMORROW-DAY"
    DATETIME_TOMORROW_DAY_ORDINAL = "DATETIME-TOMORROW-DAY-ORDINAL"
    DATETIME_TOMORROW_WEEKDAY = "DATETIME-TOMORROW-WEEKDAY"
    DATETIME_TOMORROW_MONTH = "DATETIME-TOMORROW-MONTH"
    DATETIME_TOMORROW_YEAR = "DATETIME-TOMORROW-YEAR"
    DATETIME_YESTERDAY_DAY = "DATETIME-YESTERDAY-DAY"
    DATETIME_YESTERDAY_DAY_ORDINAL = "DATETIME-YESTERDAY-DAY-ORDINAL"
    DATETIME_YESTERDAY_WEEKDAY = "DATETIME-YESTERDAY-WEEKDAY"
    DATETIME_YESTERDAY_MONTH = "DATETIME-YESTERDAY-MONTH"
    DATETIME_YESTERDAY_YEAR = "DATETIME-YESTERDAY-YEAR"

    CALENDAR_NOW = "CALENDAR-NOW"
    CALENDAR_NOW_TIME = "CALENDAR-NOW-TIME"
    CALENDAR_NEXT = "CALENDAR-NEXT"
    CALENDAR_NEXT_TIME = "CALENDAR-NEXT-TIME"
    CALENDAR_NEXT_TODAY = "CALENDAR-NEXT-TODAY"
    CALENDAR_NEXT_TODAY_TIME = "CALENDAR-NEXT-TODAY-TIME"
    CALENDAR_NEXT_TOMORROW = "CALENDAR-NEXT-TOMORROW"
    CALENDAR_NEXT_TOMORROW_TIME = "CALENDAR-NEXT-TOMORROW-TIME"
    CALENDAR_LAST = "CALENDAR-LAST"
    CALENDAR_LAST_TIME = "CALENDAR-LAST-TIME"
    CALENDAR_LAST_YESTERDAY = "CALENDAR-LAST-YESTERDAY"
    CALENDAR_LAST_YESTERDAY_TIME = "CALENDAR-LAST-YESTERDAY-TIME"
    CALENDAR_LAST_TOMORROW = "CALENDAR-LAST-TOMORROW"
    CALENDAR_LAST_TOMORROW_TIME = "CALENDAR-LAST-TOMORROW-TIME"
    CALENDAR_LAST_TODAY = "CALENDAR-LAST-TODAY"
    CALENDAR_LAST_TODAY_TIME = "CALENDAR-LAST-TODAY-TIME"

    REPORT_LAST_MEDICATION_VALUE = "REPORT-LAST-MEDICATION-VALUE"
    REPORT_LAST_MEDICATION_TIME = "REPORT-LAST-MEDICATION-TIME"
    REPORT_LAST_SLEEP_VALUE = "REPORT-LAST-SLEEP-VALUE"
    REPORT_LAST_SLEEP_TIME = "REPORT-LAST-SLEEP-TIME"
    REPORT_LAST_MEAL_VALUE = "REPORT-LAST-MEAL-VALUE"
    REPORT_LAST_MEAL_TIME = "REPORT-LAST-MEAL-TIME"
    REPORT_LAST_ACTIVITY_VALUE = "REPORT-LAST-ACTIVITY-VALUE"
    REPORT_LAST_ACTIVITY_TIME = "REPORT-LAST-ACTIVITY-TIME"
    REPORT_LAST_MOOD_VALUE = "REPORT-LAST-MOOD-VALUE"
    REPORT_LAST_MOOD_TIME = "REPORT-LAST-MOOD-TIME"

    WEATHER_NOW = "WEATHER-NOW"
    WEATHER_NOW_TEMP = "WEATHER-NOW-TEMP"
    WEATHER_NOW_TEMP_FEEL = "WEATHER-NOW-TEMP-FEEL"
    WEATHER_NOW_TEMP_MIN = "WEATHER-NOW-TEMP-MIN"
    WEATHER_NOW_TEMP_MAX = "WEATHER-NOW-TEMP-MAX"
    WEATHER_NOW_PRESSURE = "WEATHER-NOW-PRESSURE"
    WEATHER_NOW_HUMIDITY = "WEATHER-NOW-HUMIDITY"
    WEATHER_NOW_WIND_SPEED = "WEATHER-NOW-WIND-SPEED"
    WEATHER_NOW_WIND_DIRECTION = "WEATHER-NOW-WIND-DIRECTION"
    WEATHER_NOW_VISIBILITY = "WEATHER-NOW-VISIBILITY"
    WEATHER_NOW_CLOUDS = "WEATHER-NOW-CLOUDS"
    WEATHER_NOW_RAIN = "WEATHER-NOW-RAIN"
    WEATHER_NOW_SNOW = "WEATHER-NOW-SNOW"

    WEATHER_FORECAST_NEXT_HOUR = "WEATHER-FORECAST-NEXT-HOUR"
    WEATHER_FORECAST_NEXT_HOUR_TEMP = "WEATHER-FORECAST-NEXT-HOUR-TEMP"
    WEATHER_FORECAST_NEXT_HOUR_TEMP_FEEL = "WEATHER-FORECAST-NEXT-HOUR-TEMP-FEEL"
    WEATHER_FORECAST_NEXT_HOUR_TEMP_MIN = "WEATHER-FORECAST-NEXT-HOUR-TEMP-MIN"
    WEATHER_FORECAST_NEXT_HOUR_TEMP_MAX = "WEATHER-FORECAST-NEXT-HOUR-TEMP-MAX"
    WEATHER_FORECAST_NEXT_HOUR_PRESSURE = "WEATHER-FORECAST-NEXT-HOUR-PRESSURE"
    WEATHER_FORECAST_NEXT_HOUR_HUMIDITY = "WEATHER-FORECAST-NEXT-HOUR-HUMIDITY"
    WEATHER_FORECAST_NEXT_HOUR_WIND_SPEED = "WEATHER-FORECAST-NEXT-HOUR-WIND-SPEED"
    WEATHER_FORECAST_NEXT_HOUR_WIND_DIRECTION = "WEATHER-FORECAST-NEXT-HOUR-WIND-DIRECTION"
    WEATHER_FORECAST_NEXT_HOUR_VISIBILITY = "WEATHER-FORECAST-NEXT-HOUR-VISIBILITY"
    WEATHER_FORECAST_NEXT_HOUR_CLOUDS = "WEATHER-FORECAST-NEXT-HOUR-CLOUDS"
    WEATHER_FORECAST_NEXT_HOUR_RAIN = "WEATHER-FORECAST-NEXT-HOUR-RAIN"
    WEATHER_FORECAST_NEXT_HOUR_SNOW = "WEATHER-FORECAST-NEXT-HOUR-SNOW"

    WEATHER_FORECAST_AFTER_NEXT_HOUR = "WEATHER-FORECAST-AFTER-NEXT-HOUR"
    WEATHER_FORECAST_AFTER_NEXT_HOUR_TEMP = "WEATHER-FORECAST-AFTER-NEXT-HOUR-TEMP"
    WEATHER_FORECAST_AFTER_NEXT_HOUR_TEMP_FEEL = "WEATHER-FORECAST-AFTER-NEXT-HOUR-TEMP-FEEL"
    WEATHER_FORECAST_AFTER_NEXT_HOUR_TEMP_MIN = "WEATHER-FORECAST-AFTER-NEXT-HOUR-TEMP-MIN"
    WEATHER_FORECAST_AFTER_NEXT_HOUR_TEMP_MAX = "WEATHER-FORECAST-AFTER-NEXT-HOUR-TEMP-MAX"
    WEATHER_FORECAST_AFTER_NEXT_HOUR_PRESSURE = "WEATHER-FORECAST-AFTER-NEXT-HOUR-PRESSURE"
    WEATHER_FORECAST_AFTER_NEXT_HOUR_HUMIDITY = "WEATHER-FORECAST-AFTER-NEXT-HOUR-HUMIDITY"
    WEATHER_FORECAST_AFTER_NEXT_HOUR_WIND_SPEED = "WEATHER-FORECAST-AFTER-NEXT-HOUR-WIND-SPEED"
    WEATHER_FORECAST_AFTER_NEXT_HOUR_WIND_DIRECTION = "WEATHER-FORECAST-AFTER-NEXT-HOUR-WIND-DIRECTION"
    WEATHER_FORECAST_AFTER_NEXT_HOUR_VISIBILITY = "WEATHER-FORECAST-AFTER-NEXT-HOUR-VISIBILITY"
    WEATHER_FORECAST_AFTER_NEXT_HOUR_CLOUDS = "WEATHER-FORECAST-AFTER-NEXT-HOUR-CLOUDS"
    WEATHER_FORECAST_AFTER_NEXT_HOUR_RAIN = "WEATHER-FORECAST-AFTER-NEXT-HOUR-RAIN"
    WEATHER_FORECAST_AFTER_NEXT_HOUR_SNOW = "WEATHER-FORECAST-AFTER-NEXT-HOUR-SNOW"

    WEATHER_FORECAST_THIS_MORNING = "WEATHER-FORECAST-THIS-MORNING"
    WEATHER_FORECAST_THIS_MORNING_TEMP = "WEATHER-FORECAST-THIS-MORNING-TEMP"
    WEATHER_FORECAST_THIS_MORNING_TEMP_FEEL = "WEATHER-FORECAST-THIS-MORNING-TEMP-FEEL"
    WEATHER_FORECAST_THIS_MORNING_TEMP_MIN = "WEATHER-FORECAST-THIS-MORNING-TEMP-MIN"
    WEATHER_FORECAST_THIS_MORNING_TEMP_MAX = "WEATHER-FORECAST-THIS-MORNING-TEMP-MAX"
    WEATHER_FORECAST_THIS_MORNING_PRESSURE = "WEATHER-FORECAST-THIS-MORNING-PRESSURE"
    WEATHER_FORECAST_THIS_MORNING_HUMIDITY = "WEATHER-FORECAST-THIS-MORNING-HUMIDITY"
    WEATHER_FORECAST_THIS_MORNING_WIND_SPEED = "WEATHER-FORECAST-THIS-MORNING-WIND-SPEED"
    WEATHER_FORECAST_THIS_MORNING_WIND_DIRECTION = "WEATHER-FORECAST-THIS-MORNING-WIND-DIRECTION"
    WEATHER_FORECAST_THIS_MORNING_VISIBILITY = "WEATHER-FORECAST-THIS-MORNING-VISIBILITY"
    WEATHER_FORECAST_THIS_MORNING_CLOUDS = "WEATHER-FORECAST-THIS-MORNING-CLOUDS"
    WEATHER_FORECAST_THIS_MORNING_RAIN = "WEATHER-FORECAST-THIS-MORNING-RAIN"
    WEATHER_FORECAST_THIS_MORNING_SNOW = "WEATHER-FORECAST-THIS-MORNING-SNOW"

    WEATHER_FORECAST_THIS_AFTERNOON = "WEATHER-FORECAST-THIS-AFTERNOON"
    WEATHER_FORECAST_THIS_AFTERNOON_TEMP = "WEATHER-FORECAST-THIS-AFTERNOON-TEMP"
    WEATHER_FORECAST_THIS_AFTERNOON_TEMP_FEEL = "WEATHER-FORECAST-THIS-AFTERNOON-TEMP-FEEL"
    WEATHER_FORECAST_THIS_AFTERNOON_TEMP_MIN = "WEATHER-FORECAST-THIS-AFTERNOON-TEMP-MIN"
    WEATHER_FORECAST_THIS_AFTERNOON_TEMP_MAX = "WEATHER-FORECAST-THIS-AFTERNOON-TEMP-MAX"
    WEATHER_FORECAST_THIS_AFTERNOON_PRESSURE = "WEATHER-FORECAST-THIS-AFTERNOON-PRESSURE"
    WEATHER_FORECAST_THIS_AFTERNOON_HUMIDITY = "WEATHER-FORECAST-THIS-AFTERNOON-HUMIDITY"
    WEATHER_FORECAST_THIS_AFTERNOON_WIND_SPEED = "WEATHER-FORECAST-THIS-AFTERNOON-WIND-SPEED"
    WEATHER_FORECAST_THIS_AFTERNOON_WIND_DIRECTION = "WEATHER-FORECAST-THIS-AFTERNOON-WIND-DIRECTION"
    WEATHER_FORECAST_THIS_AFTERNOON_VISIBILITY = "WEATHER-FORECAST-THIS-AFTERNOON-VISIBILITY"
    WEATHER_FORECAST_THIS_AFTERNOON_CLOUDS = "WEATHER-FORECAST-THIS-AFTERNOON-CLOUDS"
    WEATHER_FORECAST_THIS_AFTERNOON_RAIN = "WEATHER-FORECAST-THIS-AFTERNOON-RAIN"
    WEATHER_FORECAST_THIS_AFTERNOON_SNOW = "WEATHER-FORECAST-THIS-AFTERNOON-SNOW"

    WEATHER_FORECAST_THIS_EVENING = "WEATHER-FORECAST-THIS-EVENING"
    WEATHER_FORECAST_THIS_EVENING_TEMP = "WEATHER-FORECAST-THIS-EVENING-TEMP"
    WEATHER_FORECAST_THIS_EVENING_TEMP_FEEL = "WEATHER-FORECAST-THIS-EVENING-TEMP-FEEL"
    WEATHER_FORECAST_THIS_EVENING_TEMP_MIN = "WEATHER-FORECAST-THIS-EVENING-TEMP-MIN"
    WEATHER_FORECAST_THIS_EVENING_TEMP_MAX = "WEATHER-FORECAST-THIS-EVENING-TEMP-MAX"
    WEATHER_FORECAST_THIS_EVENING_PRESSURE = "WEATHER-FORECAST-THIS-EVENING-PRESSURE"
    WEATHER_FORECAST_THIS_EVENING_HUMIDITY = "WEATHER-FORECAST-THIS-EVENING-HUMIDITY"
    WEATHER_FORECAST_THIS_EVENING_WIND_SPEED = "WEATHER-FORECAST-THIS-EVENING-WIND-SPEED"
    WEATHER_FORECAST_THIS_EVENING_WIND_DIRECTION = "WEATHER-FORECAST-THIS-EVENING-WIND-DIRECTION"
    WEATHER_FORECAST_THIS_EVENING_VISIBILITY = "WEATHER-FORECAST-THIS-EVENING-VISIBILITY"
    WEATHER_FORECAST_THIS_EVENING_CLOUDS = "WEATHER-FORECAST-THIS-EVENING-CLOUDS"
    WEATHER_FORECAST_THIS_EVENING_RAIN = "WEATHER-FORECAST-THIS-EVENING-RAIN"
    WEATHER_FORECAST_THIS_EVENING_SNOW = "WEATHER-FORECAST-THIS-EVENING-SNOW"

    WEATHER_FORECAST_TOMORROW = "WEATHER-FORECAST-TOMORROW"
    WEATHER_FORECAST_TOMORROW_TEMP = "WEATHER-FORECAST-TOMORROW-TEMP"
    WEATHER_FORECAST_TOMORROW_TEMP_FEEL = "WEATHER-FORECAST-TOMORROW-TEMP-FEEL"
    WEATHER_FORECAST_TOMORROW_TEMP_MIN = "WEATHER-FORECAST-TOMORROW-TEMP-MIN"
    WEATHER_FORECAST_TOMORROW_TEMP_MAX = "WEATHER-FORECAST-TOMORROW-TEMP-MAX"
    WEATHER_FORECAST_TOMORROW_PRESSURE = "WEATHER-FORECAST-TOMORROW-PRESSURE"
    WEATHER_FORECAST_TOMORROW_HUMIDITY = "WEATHER-FORECAST-TOMORROW-HUMIDITY"
    WEATHER_FORECAST_TOMORROW_WIND_SPEED = "WEATHER-FORECAST-TOMORROW-WIND-SPEED"
    WEATHER_FORECAST_TOMORROW_WIND_DIRECTION = "WEATHER-FORECAST-TOMORROW-WIND-DIRECTION"
    WEATHER_FORECAST_TOMORROW_VISIBILITY = "WEATHER-FORECAST-TOMORROW-VISIBILITY"
    WEATHER_FORECAST_TOMORROW_CLOUDS = "WEATHER-FORECAST-TOMORROW-CLOUDS"
    WEATHER_FORECAST_TOMORROW_RAIN = "WEATHER-FORECAST-TOMORROW-RAIN"
    WEATHER_FORECAST_TOMORROW_SNOW = "WEATHER-FORECAST-TOMORROW-SNOW"

    WEATHER_FORECAST_TOMORROW_MORNING = "WEATHER-FORECAST-TOMORROW-MORNING"
    WEATHER_FORECAST_TOMORROW_MORNING_TEMP = "WEATHER-FORECAST-TOMORROW-MORNING-TEMP"
    WEATHER_FORECAST_TOMORROW_MORNING_TEMP_FEEL = "WEATHER-FORECAST-TOMORROW-MORNING-TEMP-FEEL"
    WEATHER_FORECAST_TOMORROW_MORNING_TEMP_MIN = "WEATHER-FORECAST-TOMORROW-MORNING-TEMP-MIN"
    WEATHER_FORECAST_TOMORROW_MORNING_TEMP_MAX = "WEATHER-FORECAST-TOMORROW-MORNING-TEMP-MAX"
    WEATHER_FORECAST_TOMORROW_MORNING_PRESSURE = "WEATHER-FORECAST-TOMORROW-MORNING-PRESSURE"
    WEATHER_FORECAST_TOMORROW_MORNING_HUMIDITY = "WEATHER-FORECAST-TOMORROW-MORNING-HUMIDITY"
    WEATHER_FORECAST_TOMORROW_MORNING_WIND_SPEED = "WEATHER-FORECAST-TOMORROW-MORNING-WIND-SPEED"
    WEATHER_FORECAST_TOMORROW_MORNING_WIND_DIRECTION = "WEATHER-FORECAST-TOMORROW-MORNING-WIND-DIRECTION"
    WEATHER_FORECAST_TOMORROW_MORNING_VISIBILITY = "WEATHER-FORECAST-TOMORROW-MORNING-VISIBILITY"
    WEATHER_FORECAST_TOMORROW_MORNING_CLOUDS = "WEATHER-FORECAST-TOMORROW-MORNING-CLOUDS"
    WEATHER_FORECAST_TOMORROW_MORNING_RAIN = "WEATHER-FORECAST-TOMORROW-MORNING-RAIN"
    WEATHER_FORECAST_TOMORROW_MORNING_SNOW = "WEATHER-FORECAST-TOMORROW-MORNING-SNOW"

    WEATHER_FORECAST_TOMORROW_AFTERNOON = "WEATHER-FORECAST-TOMORROW-AFTERNOON"
    WEATHER_FORECAST_TOMORROW_AFTERNOON_TEMP = "WEATHER-FORECAST-TOMORROW-AFTERNOON-TEMP"
    WEATHER_FORECAST_TOMORROW_AFTERNOON_TEMP_FEEL = "WEATHER-FORECAST-TOMORROW-AFTERNOON-TEMP-FEEL"
    WEATHER_FORECAST_TOMORROW_AFTERNOON_TEMP_MIN = "WEATHER-FORECAST-TOMORROW-AFTERNOON-TEMP-MIN"
    WEATHER_FORECAST_TOMORROW_AFTERNOON_TEMP_MAX = "WEATHER-FORECAST-TOMORROW-AFTERNOON-TEMP-MAX"
    WEATHER_FORECAST_TOMORROW_AFTERNOON_PRESSURE = "WEATHER-FORECAST-TOMORROW-AFTERNOON-PRESSURE"
    WEATHER_FORECAST_TOMORROW_AFTERNOON_HUMIDITY = "WEATHER-FORECAST-TOMORROW-AFTERNOON-HUMIDITY"
    WEATHER_FORECAST_TOMORROW_AFTERNOON_WIND_SPEED = "WEATHER-FORECAST-TOMORROW-AFTERNOON-WIND-SPEED"
    WEATHER_FORECAST_TOMORROW_AFTERNOON_WIND_DIRECTION = "WEATHER-FORECAST-TOMORROW-AFTERNOON-WIND-DIRECTION"
    WEATHER_FORECAST_TOMORROW_AFTERNOON_VISIBILITY = "WEATHER-FORECAST-TOMORROW-AFTERNOON-VISIBILITY"
    WEATHER_FORECAST_TOMORROW_AFTERNOON_CLOUDS = "WEATHER-FORECAST-TOMORROW-AFTERNOON-CLOUDS"
    WEATHER_FORECAST_TOMORROW_AFTERNOON_RAIN = "WEATHER-FORECAST-TOMORROW-AFTERNOON-RAIN"
    WEATHER_FORECAST_TOMORROW_AFTERNOON_SNOW = "WEATHER-FORECAST-TOMORROW-AFTERNOON-SNOW"

    WEATHER_FORECAST_TOMORROW_EVENING = "WEATHER-FORECAST-TOMORROW-EVENING"
    WEATHER_FORECAST_TOMORROW_EVENING_TEMP = "WEATHER-FORECAST-TOMORROW-EVENING-TEMP"
    WEATHER_FORECAST_TOMORROW_EVENING_TEMP_FEEL = "WEATHER-FORECAST-TOMORROW-EVENING-TEMP-FEEL"
    WEATHER_FORECAST_TOMORROW_EVENING_TEMP_MIN = "WEATHER-FORECAST-TOMORROW-EVENING-TEMP-MIN"
    WEATHER_FORECAST_TOMORROW_EVENING_TEMP_MAX = "WEATHER-FORECAST-TOMORROW-EVENING-TEMP-MAX"
    WEATHER_FORECAST_TOMORROW_EVENING_PRESSURE = "WEATHER-FORECAST-TOMORROW-EVENING-PRESSURE"
    WEATHER_FORECAST_TOMORROW_EVENING_HUMIDITY = "WEATHER-FORECAST-TOMORROW-EVENING-HUMIDITY"
    WEATHER_FORECAST_TOMORROW_EVENING_WIND_SPEED = "WEATHER-FORECAST-TOMORROW-EVENING-WIND-SPEED"
    WEATHER_FORECAST_TOMORROW_EVENING_WIND_DIRECTION = "WEATHER-FORECAST-TOMORROW-EVENING-WIND-DIRECTION"
    WEATHER_FORECAST_TOMORROW_EVENING_VISIBILITY = "WEATHER-FORECAST-TOMORROW-EVENING-VISIBILITY"
    WEATHER_FORECAST_TOMORROW_EVENING_CLOUDS = "WEATHER-FORECAST-TOMORROW-EVENING-CLOUDS"
    WEATHER_FORECAST_TOMORROW_EVENING_RAIN = "WEATHER-FORECAST-TOMORROW-EVENING-RAIN"
    WEATHER_FORECAST_TOMORROW_EVENING_SNOW = "WEATHER-FORECAST-TOMORROW-EVENING-SNOW"

    NEWS_TODAY_TITLE = "NEWS-TODAY-TITLE"
    NEWS_TODAY_PUBLISHED_AT = "NEWS-TODAY-PUBLISHED-AT"
    NEWS_TODAY_SOURCE = "NEWS-TODAY-SOURCE"
    NEWS_TODAY_AUTHOR = "NEWS-TODAY-AUTHOR"
    NEWS_LATEST_TITLE = "NEWS-LATEST-TITLE"
    NEWS_LATEST_PUBLISHED_AT = "NEWS-LATEST-PUBLISHED-AT"
    NEWS_LATEST_SOURCE = "NEWS-LATEST-SOURCE"
    NEWS_LATEST_AUTHOR = "NEWS-LATEST-AUTHOR"

    def __str__(self):
        return str(self.value).lower()


def get_translation(key: str, lang: str):
    available_variables = variables_df[variables_df['varname'] == key]
    variables_lang = available_variables[available_variables['lang'] == lang]
    if len(variables_lang) == 0:
        return key  # return the key if no translation is known
    return variables_lang.sample(1)['value'].to_numpy()[0]


utc_zone = dt_tz.gettz('UTC')
# https://stackoverflow.com/questions/4770297/convert-utc-datetime-string-to-local-datetime
def utc_to_tz(dt: datetime, to_zone):
    utc = dt.replace(tzinfo=utc_zone)
    return utc.astimezone(to_zone)

def utc_str_to_tz(utc_str: str, format: str, to_zone):
    dt = datetime.strptime(utc_str, format)
    return utc_to_tz(dt, to_zone)

def set_locale_with_lang(lang: str = None):
    lc = None
    if lang == "nl":
        lc = "nl_NL"
    elif lang == "en":
        lc = "en_GB"
    elif lang == "de":
        lc = "de_DE"
    else:
        lc = locale.getdefaultlocale()[0]

    locale.setlocale(locale.LC_ALL, lc+".UTF-8")


def get_calendar_vars_future(future: list, time: datetime, lang: str):
    vars_ = {}
    if not future:
        return vars_
    future.sort(key=lambda x: x['start_time'])

    if future:
        entry_next = future[0]
        vars_["CALENDAR-NEXT"] = entry_next["message"]
        vars_["CALENDAR-NEXT-TIME"] = (get_translation("at", lang) + " "
                                       + entry_next["start_time"].strftime('%H:%M'))
        if entry_next["start_time"].date() == time.date() + timedelta(days=1):
            vars_["CALENDAR-NEXT-TOMORROW"] = entry_next["message"]
            vars_["CALENDAR-NEXT-TOMORROW-TIME"] = (get_translation("tomorrow", lang) + " "
                                                    + get_translation("at", lang) + " "
                                                    + entry_next["start_time"].strftime('%H:%M'))
            vars_["CALENDAR-NEXT-TIME"] = vars_["CALENDAR-NEXT-TOMORROW-TIME"]
        entry_last = future[-1]
        vars_["CALENDAR-LAST-TOMORROW"] = entry_last["message"]
        vars_["CALENDAR-LAST-TOMORROW-TIME"] = (get_translation("tomorrow", lang) + " "
                                                + get_translation("at", lang) + " "
                                                + entry_last["start_time"].strftime('%H:%M'))

    return vars_


def get_calendar_vars_past(past: list, time: datetime, lang: str):
    vars_ = {}
    if not past:
        return vars_
    past.sort(key=lambda x: x['start_time'])

    if past:
        entry_last = past[-1]
        vars_["CALENDAR-LAST"] = entry_last["message"]
        vars_["CALENDAR-LAST-TIME"] = (get_translation("at", lang) + " "
                                       + entry_last["start_time"].strftime('%H:%M'))
        if entry_last["start_time"].date() == time.date() - timedelta(days=1):
            vars_["CALENDAR-LAST-YESTERDAY"] = entry_last["message"]
            vars_["CALENDAR-LAST-YESTERDAY-TIME"] = (get_translation("yesterday", lang) + " "
                                                     + get_translation("at", lang) + " "
                                                     + entry_last["start_time"].strftime('%H:%M'))
            vars_["CALENDAR-LAST-TIME"] = vars_["CALENDAR-LAST-YESTERDAY-TIME"]

    return vars_


def get_calendar_vars_today(today: list, time: datetime, lang: str):
    vars_ = {}
    if not today:
        return vars_
    today.sort(key=lambda x: x['start_time'])

    if today:
        entry_last = today[-1]
        vars_["CALENDAR-LAST-TODAY"] = entry_last["message"]
        vars_["CALENDAR-LAST-TODAY-TIME"] = (get_translation("at", lang) + " "
                                             + entry_last["start_time"].strftime('%H:%M'))
    if today and today[0]["start_time"] < time:
        entry_now = today.pop(0)
        vars_["CALENDAR-NOW"] = entry_now["message"]
        vars_["CALENDAR-NOW-TIME"] = (get_translation("until", lang) + " "
                                      + entry_now["end_time"].strftime('%H:%M'))
    for t in today:
        if today[0]["start_time"] < time:
            today.pop(0)
    if today:
        entry_next = today[0]
        vars_["CALENDAR-NEXT-TODAY"] = entry_next["message"]
        vars_["CALENDAR-NEXT-TODAY-TIME"] = (get_translation("at", lang) + " "
                                             + entry_next["start_time"].strftime('%H:%M'))
        entry_next = today[0]
        vars_["CALENDAR-NEXT"] = entry_next["message"]
        vars_["CALENDAR-NEXT-TIME"] = (get_translation("at", lang) + " "
                                       + entry_next["start_time"].strftime('%H:%M'))
    return vars_


# https://docs.python.org/3/library/datetime.html#format-codes
async def get_calendar(tablet_id: str, controller, lang: str):
    rnow = datetime.utcnow()

    calendar_today = await controller.get_calendar_data(tablet_id, day=rnow)
    #calendar_yesterday = await controller.get_calendar_data(tablet_id, day=rnow - timedelta(days=1))
    #calendar_tomorrow = await controller.get_calendar_data(tablet_id, day=rnow + timedelta(days=1))
    #calendar = calendar_yesterday + calendar_today + calendar_tomorrow
    calendar = calendar_today

    vars_ = {}
    if not calendar:
        return vars_

    to_zone = dt_tz.gettz("Europe/Amsterdam")
    for i in range(len(calendar)):
        if "entry" in calendar[i] and "user" in calendar[i]["entry"] and "timezone" in calendar[i]["entry"]["user"]:
            to_zone = dt_tz.gettz("Europe/Amsterdam")
            break

    time = utc_to_tz(rnow, to_zone)
    past, today, future = [], [], []
    for v in calendar:
        entry = {"message": v["entry"]["message"].lower(),
                 "start_time": utc_str_to_tz(v["entry"]["startTime"], "%Y-%m-%dT%H:%M:%SZ", to_zone)}
        if "end_time" in v["entry"]:
            entry["end_time"] = utc_str_to_tz(v["entry"]["hide"], "%Y-%m-%dT%H:%M:%SZ", to_zone)
        else:
            entry["end_time"] = entry["start_time"] + timedelta(
                minutes=30)  # Here we arbitrarily set default duration to 10 mins
        if entry["end_time"] < time:
            past.append(entry)
        elif entry["start_time"].date() == time.date():
            today.append(entry)
        else:
            future.append(entry)

    vars_.update(get_calendar_vars_past(past, time, lang=lang))
    vars_.update(get_calendar_vars_future(future, time, lang=lang))
    vars_.update(get_calendar_vars_today(today, time, lang=lang))
    return vars_


async def get_reports(tablet_id: str, controller, lang: str):
    rnow = datetime.utcnow()

    reports_today = await controller.get_report_data(tablet_id, day=rnow)
    reports = reports_today["last_24h"]
    future = reports_today["future"]

    vars_ = {}
    if not reports:
        return vars_

    to_zone = dt_tz.gettz("Europe/Amsterdam")
    time = utc_to_tz(rnow, to_zone)

    valmap_binary = {0: "no", 1: "yes"}
    valmap_scale = {1: "bad", 2: "okay", 3: "good", 4: "great"}

    for v in reports:
        report_type = v["type"]
        reported_at = utc_str_to_tz(v["reportedAt"], "%Y-%m-%dT%H:%M:%SZ", to_zone)
        if report_type == "activity":
            vars_[Defaults.REPORT_LAST_ACTIVITY_VALUE.value] = get_translation(valmap_binary[int(v["value"])], lang)
            vars_[Defaults.REPORT_LAST_ACTIVITY_TIME.value] = (get_translation("at", lang) + " " + reported_at.strftime('%H:%M'))
        if report_type == "mood":
            vars_[Defaults.REPORT_LAST_MOOD_VALUE.value] = get_translation(valmap_scale[int(v["value"])], lang)
            vars_[Defaults.REPORT_LAST_MOOD_TIME.value] = (get_translation("at", lang) + " " + reported_at.strftime('%H:%M'))
        if report_type == "medication":
            vars_[Defaults.REPORT_LAST_MEDICATION_VALUE.value] = get_translation(valmap_binary[int(v["value"])], lang)
            vars_[Defaults.REPORT_LAST_MEDICATION_TIME.value] = (get_translation("at", lang) + " " + reported_at.strftime('%H:%M'))
        if report_type == "meal":
            vars_[Defaults.REPORT_LAST_MEAL_VALUE.value] = get_translation(valmap_binary[int(v["value"])], lang)
            vars_[Defaults.REPORT_LAST_MEAL_TIME.value] = (get_translation("at", lang) + " " + reported_at.strftime('%H:%M'))
        if report_type == "sleep_quality":
            vars_[Defaults.REPORT_LAST_SLEEP_VALUE.value] = get_translation(valmap_scale[int(v["value"])], lang)
            vars_[Defaults.REPORT_LAST_SLEEP_TIME.value] = (get_translation("at", lang) + " " + reported_at.strftime('%H:%M'))

    return vars_

async def _get_weather(weather: dict, lang: str, tag_prepend: str):
    vars_ = {}

    if "weather" in weather and weather["weather"]:
        w = weather["weather"][0]  # there can be multiple weathers i.e. rainy and cloudy
        if "description" in w:
            vars_[tag_prepend] = w["description"]

    if "main" in weather:
        m = weather["main"]
        if "temp" in m:
            vars_[tag_prepend+"-TEMP"] = str(round(m["temp"], 1)) + get_translation("°", lang)
        if "feels_like" in m:
            vars_[tag_prepend+"-TEMP-FEEL"] = str(round(m["feels_like"], 1)) + get_translation("°", lang)
        if "tem_min" in m:
            vars_[tag_prepend+"-TEMP-MIN"] = str(round(m["temp_min"], 1)) + get_translation("°", lang)
        if "temp_max" in m:
            vars_[tag_prepend+"-TEMP-MAX"] = str(round(m["temp_max"], 1)) + get_translation("°", lang)
        if "humidity" in m:
            vars_[tag_prepend+"-HUMIDITY"] = str(int(round(m["humidity"], 0))) + get_translation("%", lang)
        if "pressure" in m:
            vars_[tag_prepend+"-PRESSURE"] = str(int(round(m["pressure"], 0))) + get_translation("hPa", lang)

    if "visibility" in weather:
        vars_[tag_prepend+"-VISIBILITY"] = str(int(round(weather["visibility"], 0))) + get_translation("m", lang)

    if "wind" in weather:
        w = weather["wind"]
        if "speed" in w:
            vars_[tag_prepend+"-WIND-SPEED"] = str(int(round(w["speed"], 0))) + " " + get_translation("meters_per_second", lang)
        if "deg" in w:
            vars_[tag_prepend+"-WIND-DIRECTION"] = str(int(round(w["deg"], 0))) + get_translation("°", lang)

    if "clouds" in weather and "all" in weather["clouds"]:
        vars_[tag_prepend+"-CLOUDS"] = str(int(round(weather["clouds"]["all"], 0))) + get_translation("%", lang)
    if "rain" in weather and "1h" in weather["rain"]:
        vars_[tag_prepend+"-RAIN"] = str(round(weather["rain"]["1h"], 1)) + get_translation("mm", lang)
    if "snow" in weather and "1h" in weather["snow"]:
        vars_[tag_prepend+"-SNOW"] = str(round(weather["snow"]["1h"], 1)) + get_translation("mm", lang)
    return vars_


async def get_weather_now(tablet_id: str, controller, lang: str):
    weather = await controller.get_weather_now_data(tablet_id, lang=lang)
    return await _get_weather(weather, lang, "WEATHER-NOW")


async def get_weather_forecast(tablet_id: str, controller, lang: str):
    weather = await controller.get_weather_forecast_data(tablet_id, lang=lang)
    vars_ = {}

    to_zone = dt_tz.gettz("Europe/Amsterdam")
    time = utc_to_tz(datetime.utcnow(), to_zone)
    today = time.date()
    tomorrow = time.date() + timedelta(days=1)
    next_hour = time + timedelta(minutes=179) # the weather is predicted in timespans of 3 hours
    # weather_items = []

    if "list" in weather and weather["list"]:
        vars_.update(await _get_weather(weather["list"][0], lang=lang, tag_prepend="WEATHER-FORECAST-NEXT-HOUR"))
        vars_.update(await _get_weather(weather["list"][1], lang=lang, tag_prepend="WEATHER-FORECAST-AFTER-NEXT-HOUR"))

        for i, item in enumerate(weather["list"]):
            # vars_item = get_weather_now(item, lang=lang, tag_prepend="WEATHER-FORECAST")

            timestamp = utc_str_to_tz(item["dt_txt"], '%Y-%m-%d %H:%M:%S', to_zone)
            # weather_items.append({"time": timestamp, "index": i})

            if timestamp.date() == today:
                if "WEATHER-FORECAST-THIS-MORNING" not in vars_ and (timestamp.hour >= 6 and timestamp.hour < 12):
                    vars_.update(await _get_weather(item, lang=lang, tag_prepend="WEATHER-FORECAST-THIS-MORNING"))

                if "WEATHER-FORECAST-THIS-AFTERNOON" not in vars_ and (timestamp.hour >= 12 and timestamp.hour <= 17):
                    vars_.update(await _get_weather(item, lang=lang, tag_prepend="WEATHER-FORECAST-THIS-AFTERNOON"))

                if "WEATHER-FORECAST-THIS-EVENING" not in vars_ and (timestamp.hour >= 17 and timestamp.hour <= 21):
                    vars_.update(await _get_weather(item, lang=lang, tag_prepend="WEATHER-FORECAST-THIS-EVENING"))

            elif timestamp.date() == tomorrow:
                if "WEATHER-FORECAST-TOMORROW" not in vars_ and (timestamp.hour >= 6 and timestamp.hour <= 18):
                    vars_.update(await _get_weather(item, lang=lang, tag_prepend="WEATHER-FORECAST-TOMORROW"))

                if "WEATHER-FORECAST-TOMORROW-MORNING" not in vars_ and (timestamp.hour >= 6 and timestamp.hour < 12):
                    vars_.update(await _get_weather(item, lang=lang, tag_prepend="WEATHER-FORECAST-TOMORROW-MORNING"))

                if "WEATHER-FORECAST-TOMORROW-AFTERNOON" not in vars_ and (timestamp.hour >= 12 and timestamp.hour <= 17):
                    vars_.update(await _get_weather(item, lang=lang, tag_prepend="WEATHER-FORECAST-TOMORROW-AFTERNOON"))

                if "WEATHER-FORECAST-TOMORROW-EVENING" not in vars_ and (timestamp.hour >= 17 and timestamp.hour <= 21):
                    vars_.update(await _get_weather(item, lang=lang, tag_prepend="WEATHER-FORECAST-TOMORROW-EVENING"))

    # weather_items.sort(key=lambda x: x['time'])
    # print(weather_items)
    return vars_


async def get_news_article(article: dict, lang: str, tag_prepend: str):
    vars_ = {}

    if article["title"]:
        if re.search(' - [^\.]+\w', article["title"]):
            vars_[tag_prepend+"-TITLE"] = article["title"].split(" - ")[0]
        elif re.search(' — [^\.]+\w', article["title"]):
            vars_[tag_prepend+"-TITLE"] = article["title"].split(" — ")[0]
        else:
            print(article["title"])
            vars_[tag_prepend + "-TITLE"] = article["title"]
    else:
        return vars_

    if article["author"]:
        splt = article["author"].split(",")
        splt = [s.strip().capitalize() for s in splt]
        if len(splt) > 1:
            jin = ", ".join(splt[:-1]) + " " + get_translation("and", lang) + " " + splt[-1]
            vars_[tag_prepend + "-AUTHOR"] = jin
        else:
            vars_[tag_prepend + "-AUTHOR"] = splt[0]


    if article["publishedAt"]:
        vars_[tag_prepend + "-PUBLISHED-AT"] = (get_translation("at", lang) + " "
                                       + article["publishedAt"].strftime('%H:%M'))

    if article["source"]["name"]:
        name = article["source"]["name"].capitalize()
        if "ww." in article["source"]["name"]:
            splt = article["source"]["name"].split("ww.")
            vars_[tag_prepend+"-SOURCE"] = splt[1].capitalize() if len(splt) > 1 else name
        else:
            vars_[tag_prepend+"-SOURCE"] = name

    url = article["url"]

    return vars_


async def get_news(tablet_id: str, controller, lang: str):
    news = await controller.get_news_data(tablet_id, lang=lang)
    vars_ = {}

    to_zone = dt_tz.gettz("Europe/Amsterdam")
    time = utc_to_tz(datetime.utcnow(), to_zone)
    today = time.date()
    yesterday = time.date() - timedelta(days=1)

    if "articles" in news and news["articles"]:
        for article in news["articles"]:
            if article["publishedAt"]:
                try:
                    article["publishedAt"] = utc_str_to_tz(article["publishedAt"], '%Y-%d-%mT%H:%M:%SZ', to_zone)
                except Exception as e:
                    article["publishedAt"] = utc_str_to_tz(article["publishedAt"], '%Y-%m-%dT%H:%M:%SZ', to_zone)

                if "NEWS-TODAY-TITLE" not in vars_ and article["publishedAt"].date() == time.date():
                    vars_.update(await get_news_article(article, lang, "NEWS-TODAY"))

        vars_.update(await get_news_article(news["articles"][0], lang, "NEWS-LATEST"))

    return vars_


def get_daypart(lang: str):
    to_zone = dt_tz.gettz("Europe/Amsterdam")
    time = utc_to_tz(datetime.utcnow(), to_zone)
    key = defaults["DATETIME-NOW-DAYPART"]

    if time.hour >= 6 and time.hour < 12:
        key = "morning"
    elif time.hour >= 12 and time.hour < 17:
        key = "afternoon"
    elif time.hour >= 17 and time.hour < 21:
        key = "evening"
    elif time.hour >= 21 or time.hour < 6:
        key = "night"

    # https://docs.python.org/3/library/datetime.html#format-codes
    vars_ = {"DATETIME-NOW-DAYPART": get_translation(key, lang),
             "DATETIME-NOW-TIME": time.strftime('%H:%M'),
             "DATETIME-NOW-HOUR": time.strftime('%I'),
             "DATETIME-NOW-MINUTE": time.strftime('%M'),
             "DATETIME-NOW-SECOND": time.strftime('%S')
             }

    return vars_


async def _decode_datetime(time, lang: str, tag_prepend: str):
    set_locale_with_lang(lang)

    # https://docs.python.org/3/library/datetime.html#format-codes
    vars_ = {tag_prepend + "-MONTH": time.strftime('%B'),
             tag_prepend + "-WEEKDAY": time.strftime('%A'),
             tag_prepend + "-YEAR": time.strftime('%Y'),
             tag_prepend + "-DAY": time.strftime('%d')}

    if lang == "nl":
        vars_[tag_prepend + "-DAY-ORDINAL"] = time.strftime('%d') + "e"
    else:  # default to english if we dont know
        vars_[tag_prepend + "-DAY-ORDINAL"] = inf_eng.ordinal(  (int( time.strftime('%d') )  ) )

    set_locale_with_lang()
    return vars_


async def get_datetime(tablet_id: str, controller, lang: str):
    vars_ = get_daypart(lang)

    to_zone = dt_tz.gettz("Europe/Amsterdam")
    today = utc_to_tz(datetime.utcnow(), to_zone)
    vars_.update(await _decode_datetime(today, lang, "DATETIME-TODAY"))
    vars_.update(await _decode_datetime(today + timedelta(days=1), lang, "DATETIME-TOMORROW"))
    vars_.update(await _decode_datetime(today - timedelta(days=1), lang, "DATETIME-YESTERDAY"))

    return vars_


async def get_client(tablet_id: str, controller, lang: str):
    return await controller.get_client_data(tablet_id)


async def fill(message_in: str, tablet_id: str, controller, lang: str):
    to_fill = set(re.findall('\["[^\]]+"\]', message_in))
    to_fill = [x[2:-2] for x in to_fill]
    if not to_fill:
        return message_in

    env = await get_vars(to_fill, tablet_id, controller, lang)

    for key in capitalize:  # capitalize specified variables
        if key in env:
            env[key] = " ".join(x.capitalize() for x in env[key].split(" "))

    message_out = str(message_in)
    for key in env.keys():  # replace variable inserts
        message_out = message_out.replace('["' + key + '"]', str(env[key]))

    return message_out


async def get_vars(to_get: list, tablet_id: str, controller, lang: str):
    env = {}
    for key in to_get:
        if key in defaults:
             env[key] = get_translation(defaults[key], lang)  # load relevant defaults (translated)
        else:
            env[key] = MISSING_VAL

    joined_get = " ".join(to_get)
    if 'CLIENT' in joined_get:
        env.update(await get_client(tablet_id, controller, lang=lang))

    if 'DATETIME' in joined_get:
        env.update(await get_datetime(tablet_id, controller, lang=lang))

    if 'CALENDAR' in joined_get:
        calendar_vars = await get_calendar(tablet_id, controller, lang=lang)
        for t in to_get:
            if t in calendar_vars.keys():
                env[t] = calendar_vars[t]

    if 'REPORT' in joined_get:
        report_vars = await get_reports(tablet_id, controller, lang=lang)
        for t in to_get:
            if t in report_vars.keys():
                env[t] = report_vars[t]

    if 'WEATHER-NOW' in joined_get:
        print('weather')
        weather_now_vars = await get_weather_now(tablet_id, controller, lang=lang)
        print(weather_now_vars)
        for t in to_get:
            if t in weather_now_vars.keys():
                env[t] = weather_now_vars[t]

    if 'WEATHER-FORECAST' in joined_get:
        weather_forecast_vars = await get_weather_forecast(tablet_id, controller, lang=lang)
        for t in to_get:
            if t in weather_forecast_vars.keys():
                env[t] = weather_forecast_vars[t]

    if 'NEWS' in joined_get:
        news_vars = await get_news(tablet_id, controller, lang=lang)
        for t in to_get:
            if t in news_vars.keys():
                env[t] = news_vars[t]

    return env