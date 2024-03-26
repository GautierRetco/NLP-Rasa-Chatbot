import pandas as pd
import spacy
from fuzzywuzzy import process
import joblib

import re
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()

def find_genre(sentence, expanded_keywords):
    words = [lemmatizer.lemmatize(word.lower()) for word in re.split(r'\W+', sentence) if word]
    words = [word for word in words if word not in ['film', 'movie']]
    for genre, keywords in expanded_keywords.items():
        if any(word in words for word in keywords):
            return genre
    return None


def extract_entities_from_text(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    entities = [ent.text for ent in doc.ents]
    return entities, len(entities)>0

def find_closest_match_fuzzy(input_entity, database_entities):
    closest_match, score = process.extractOne(input_entity, database_entities)
    if score < 70:  
        return None  
    return closest_match

def get_list_data (column_name, data) :
    liste_data = set()
    for genres_list in data[column_name]:
        genres_list = eval(genres_list)  
        liste_data.update(genres_list)
    return liste_data

def similarity_extraction_in_dict(dictionnary, data,expanded_keywords):
    new_dict = {}
    failed_extractions = []
    for key, value in dictionnary.items():
        if isinstance(value, str) and key !='topic' and key !='genre':
            entities, extracted = extract_entities_from_text(value)
            if extracted:
                entity = entities[0]
                if key == 'target_movie_title':
                    entity = find_closest_match_fuzzy(entity, data['original_title'].tolist())
                elif key =='director': 
                    all_directors = get_list_data('director', data)
                    entity = find_closest_match_fuzzy(entity, all_directors)
                else : 
                    entity = entity
                new_dict[key]= entity
            else : 
                failed_extractions.append(value)
        elif isinstance(value, dict):
            new_dict[key], failed_extractions = similarity_extraction_in_dict(value,data,expanded_keywords)
        elif isinstance(value,list):
            new_entities = []
            for elem in value : 
                entities, extracted = extract_entities_from_text(elem)
                entity = entities[0]
                all_actors = get_list_data('cast', data)
                entity = find_closest_match_fuzzy(entity, all_actors)
                new_entities.append(entity)
            new_dict[key]= new_entities
        elif isinstance(value, str) and key == 'genre': 
            # expanded_keywords = joblib.load('expanded_keywords.pkl')
            entity = find_genre(value,expanded_keywords)
            new_dict[key]= entity
        else:
            new_dict[key] = value
    return new_dict, failed_extractions

def get_recommendations_from_title(dict, data,cos_sim):
    title = dict['target_movie_title']
    indices = pd.Series(data.index, index=data['original_title']).drop_duplicates()
    # Get the index of the movie that matches the title
    index = indices[title]
    # Some movies have the same name we will keep only the most popular movie with this name
    if isinstance(index, pd.Series):
        popularity = 0
        for id in index : 
            current_popularity = data['popularity'][id]
            if current_popularity > popularity : 
                popularity = current_popularity
                index = id

    # Apply filters before computing similarity
    filtered_data = data.copy()
    for key, value in dict.items():
        if 'set' == key : 
            for second_key, second_value in value.items() :
                if 'cast' == second_key: 
                    filtered_data = filter_by_cast(filtered_data, second_value)
                else : 
                    filtered_data = filter_by_director(filtered_data, second_value)
        if 'genre' == key :
            filtered_data = filter_by_genre(filtered_data, value)
                    
    filtered_indices = filtered_data.index.tolist()
    # cos_sim = joblib.load('matrix_similarity.pkl')
    # Get the pairwise similarity scores of all movies with that movie
    sim_scores = [(i, cos_sim[index][i]) for i in filtered_indices]
    # Sort the movies based on the similarity scores
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    similar_movies = []
    # Loop until we have at least 20 similar movies or we have checked all movies
    i = 0
    while len(similar_movies) < 20 and i < len(sim_scores) and i < len(filtered_data):
        if data.iloc[sim_scores[i][0]]['original_title'] != title:
            similar_movies.append((sim_scores[i][0], sim_scores[i][1]))
        i += 1

    # Get the movie indices
    movie_indices = [i[0] for i in similar_movies]

    # Return the top 20 most similar movies after applying filters
    return list(set(data['original_title'].iloc[movie_indices].head(20).tolist()))


def filter_by_cast(data, value):
    if  isinstance(value, list):
        mask = data['cast'].apply(lambda x: all(actor in x for actor in value))
        filtered_data = data[mask]        
    else : 
        mask = data['cast'].apply(lambda x: value in x)
        filtered_data = data[mask]
    return filtered_data


def filter_by_director(data, value):
    mask = data['director'].apply(lambda x: value in x)
    filtered_data = data[mask]
    return filtered_data

def filter_by_genre(data, value):
    mask = data['genres'].apply(lambda x: value in x)
    filtered_data = data[mask]
    return filtered_data

def get_recommendations(dictionnary, data, cos_sim, expanded_keywords):
    final_dictionnary, failed_extractions = similarity_extraction_in_dict(dictionnary,data,expanded_keywords)
    keys = final_dictionnary.keys()
    if 'target_movie_title' in keys : 
        recommendation = get_recommendations_from_title(final_dictionnary, data,cos_sim)
    else : 
        filtered_data = data.copy()
        for key, value in final_dictionnary.items():
            if 'set' == key : 
                for second_key, second_value in value.items() :
                    if 'cast' ==second_key: 
                        filtered_data =  filter_by_cast(filtered_data, second_value)
                    else: 
                        filtered_data = filter_by_director(filtered_data, second_value)
            if 'genre' ==key : 
                filtered_data = filter_by_genre(filtered_data, value)
        filtered_data = filtered_data.sort_values(by='popularity', ascending=False)
        recommendation = filtered_data['original_title'].head(20).tolist()
    return recommendation, failed_extractions, final_dictionnary

