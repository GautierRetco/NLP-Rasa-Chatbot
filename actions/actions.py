from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import os
import sys
import pandas as pd
import joblib

sys.path.append(os.path.abspath('recommendation_models'))

import recommendation
data = pd.read_csv("./recommendation_models/final_english_dataset_with_preprocess_on_overview.csv")
cos_sim = joblib.load('./recommendation_models/matrix_similarity.pkl')

class ActionDisplayEntityHistory(Action):
    def name(self) -> Text:
        return "action_recommend_movie"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        current_directory = os.getcwd()
        print("Current Working Directory:", current_directory)
        query = {}
        set = {}
        for event in reversed(tracker.events):
            if event.get('event') == 'action' and event.get('name') == 'action_recommend_movie':
                break
            if event.get('event') == 'user':
                # Afficher le texte du chat de l'utilisateur
                dispatcher.utter_message(text=event.get('text'))
                
                intent_name = event.get('parse_data', {}).get('intent', {}).get('name')
                
                if intent_name:

                    if intent_name == "inform_movie":
                        query['target_movie_title'] = event.get('text')

                    elif intent_name == "inform_genre":
                        query['genre'] = event.get('text')

                    elif intent_name == "inform_cast":
                        if "cast" in set:
                            set["cast"].append(event.get('text'))
                        else:
                            set["cast"] = [event.get('text')]

                    elif intent_name == "inform_director":
                        set["director"] = event.get('text')

                    elif intent_name == "inform_composer":
                        set["composer"] = event.get('text')

                    elif intent_name == "inform_topic":
                        query["topic"] = event.get('text')
        if set!={}:
            query["set"] = set
        print(f"Query : {query}")
        dispatcher.utter_message(text=f"Query : {query}")
        dispatcher.utter_message(text=f"{recommendation.make_recommendation(query, data, cos_sim)}")
        return []