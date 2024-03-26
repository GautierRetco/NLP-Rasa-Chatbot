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
expanded_keywords = joblib.load('./recommendation_models/expanded_keywords.pkl')

def recommend_movies_string(movies):
    recommendation = "I can recommend you : \n"
    for i, movie in enumerate(movies, start=1):
        recommendation += f"{i}. {movie}\n"
    return recommendation

def format_list(queries):
    res = "Sorry, I didn't manage to understand : \n"
    for query in queries:
        res+='  * ' + query + '\n'
    return res

class ActionDisplayEntityHistory(Action):
    def name(self) -> Text:
        return "action_recommend_movie"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        query = {}
        set = {}
        for event in reversed(tracker.events):
            if event.get('event') == 'action' and event.get('name') == 'action_recommend_movie':
                break
            if event.get('event') == 'user':

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
        print(query)
        recommendations, failed_entities = recommendation.get_recommendations(query, data, cos_sim, expanded_keywords)
        if len(failed_entities)>0:
            dispatcher.utter_message(text = f"{format_list(failed_entities)}")
            dispatcher.utter_message(text=f"\nWithout taking it into account, {recommend_movies_string(recommendations)}\n")
            dispatcher.utter_message(text="\nTo make it easier for me, use capital letters for the beginning of names and try with quotation marks")
        else:
            dispatcher.utter_message(text=f"{recommend_movies_string(recommendations)}")
        return []