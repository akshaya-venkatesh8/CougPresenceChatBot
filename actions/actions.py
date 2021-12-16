# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import urllib.request, json 
from difflib import get_close_matches
from datetime import date, datetime

from rasa_nlu_examples.extractors.dateparser_extractor import DateparserEntityExtractor
from rasa_sdk.interfaces import Action
from rasa_sdk.events import (
    SlotSet,
    EventType,
    ActionExecuted,
    SessionStarted,
    Restarted,
    FollowupAction,
    UserUtteranceReverted,
    ObjectStringMapper
)
url_link= "https://api.presence.io/wsu/v1/events";

fieldMapper = { 'eventName': "Event Name:", 'orgName':'Organised by:', 'StartTimeHumanReadable': 'Starts at:', 'EndTimeHumanReadable': 'Ends at:', 'contactName': 'Contact:', 'location':'Location:'}

class GlobalAction(Action):

    def __init__(self) -> None:
        super().__init__()
        self.EventDict={}
        self.OrgWiseEvents={}

    def name(self) -> Text:
        return ""

    def getEvents(self):
        return self.EventDict

    def getOrgWiseEvents(self):
        return self.OrgWiseEvents
    
    def getParsedString(self, object_arr, mapper):
        return ObjectStringMapper.getString(object_arr, mapper)

    async def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        with urllib.request.urlopen(url_link) as url:
            data = json.loads(url.read().decode())
        data.sort(key = lambda x: datetime.strptime(x['startDateTimeUtc'], "%Y-%m-%dT%H:%M:%SZ"))
        for x in data:
            try:
                start_time_readable = datetime.strptime(x['startDateTimeUtc'], "%Y-%m-%dT%H:%M:%SZ").strftime("%H:%M:%S on %d %b, %Y")
                end_time_readable = datetime.strptime(x['endDateTimeUtc'], "%Y-%m-%dT%H:%M:%SZ").strftime("%H:%M:%S on %d %b, %Y")
                self.EventDict[x['eventName']]={'StartTime': datetime.strptime(x['startDateTimeUtc'], "%Y-%m-%dT%H:%M:%SZ"), 'StartTimeHumanReadable': start_time_readable,'EndTime': datetime.strptime(x['endDateTimeUtc'], "%Y-%m-%dT%H:%M:%SZ"), 'EndTimeHumanReadable': end_time_readable,'contactName':x['contactName'], 'orgName':x['organizationName'], 'location': x['location']}
                if x['organizationName'] in OrgWiseEvents:
                    self.OrgWiseEvents[x['organizationName']].append({'StartTime': datetime.strptime(x['startDateTimeUtc'], "%Y-%m-%dT%H:%M:%SZ"), 'StartTimeHumanReadable': start_time_readable,'EndTime': datetime.strptime(x['endDateTimeUtc'], "%Y-%m-%dT%H:%M:%SZ"), 'EndTimeHumanReadable': end_time_readable,'contactName':x['contactName'], 'eventName':x['eventName'], 'location': x['location']})
                else:
                    self.OrgWiseEvents[x['organizationName']] = []
                    self.OrgWiseEvents[x['organizationName']].append({'StartTime': datetime.strptime(x['startDateTimeUtc'], "%Y-%m-%dT%H:%M:%SZ"), 'StartTimeHumanReadable': start_time_readable,'EndTime': datetime.strptime(x['endDateTimeUtc'], "%Y-%m-%dT%H:%M:%SZ"), 'EndTimeHumanReadable': end_time_readable,'contactName':x['contactName'], 'eventName':x['eventName'],'location': x['location']})
            except:
                continue
  
        # current_time = datetime.now()
        # events_filtered = [EventDict[key] for key in EventDict if EventDict[key]['StartTime'] > current_time]
        return []

class EventSpecific(Action, GlobalAction):

    def name(self) -> Text:
        return "action_event_specific"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        slots = {
            'org_name': None,
            'datetime': None
        }
        eventDict = {}
        if Tracker.get_slot("org_name"):
            slot = Tracker.get_slot("org_name")
            eventDict = GlobalAction.getOrgWiseEvents()[slot]
        if eventDict and Tracker.get_slot("datetime"):
            slot = Tracker.get_slot("datetime")
            extractor = DateparserEntityExtractor({})
            dateval = extractor.process(slot)
            eventDict = [eventDict[key] for key in eventDict if eventDict[key]['StartTime'] > dateval]
        if eventDict:
            dispatcher.utter_message("Here are some events:" + GlobalAction.getParsedString(eventDict, fieldMapper))
        else:
            dispatcher.utter_message("No events to report.")
        return []
class EventDetails(Action, GlobalAction):

    def name(self) -> Text:
        return "action_event_details"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        eventDict = GlobalAction.getEvents()
        events_filtered = [eventDict[key] for key in eventDict if eventDict[key]['StartTime'] > datetime.now()]
        if len(events_filtered) > 5: events_filtered = events_filtered[:5]
        dispatcher.utter_message("Here are some events:" + GlobalAction.getParsedString(events_filtered, fieldMapper))
        return []


