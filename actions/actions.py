from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class ActionDisplayEntityHistory(Action):
    def name(self) -> Text:
        return "action_recommend_movie"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        entity_history = {}
        for event in reversed(tracker.events):
            if event.get('event') == 'action' and event.get('name') == 'action_recommend_movie':
                break
            if 'parse_data' in event and 'entities' in event['parse_data']:
                for entity in event['parse_data']['entities']:
                    entity_name = entity['entity']
                    entity_value = entity['value']
                    if entity_name not in entity_history:
                        entity_history[entity_name] = [entity_value]
                    else:
                        if entity_value not in entity_history[entity_name]:
                            entity_history[entity_name].append(entity_value)

        if entity_history:
            for entity_name, values in entity_history.items():
                dispatcher.utter_message(f"Historique des valeurs pour l'entité '{entity_name}': {', '.join(values)}")
        else:
            dispatcher.utter_message("Aucune entité n'a été détectée dans les messages précédents de la conversation.")

        return []