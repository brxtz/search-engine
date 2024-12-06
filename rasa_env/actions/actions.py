# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []
from dotenv import load_dotenv
import mysql.connector
import requests
import os
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from mysql.connector import Error
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


load_dotenv()

class ActionSearchSearXNG(Action):
    def name(self) -> str:
        return "action_search_searxng"

    def run(self, dispatcher: CollectingDispatcher, tracker, domain):
        query = tracker.get_slot("user_query")

        if not query:
            dispatcher.utter_message(text="No query provided.")
            return []

        searxng_url = "https://zousearch.com/search"
        params = {
                "q": query,
                "format": "json",
                "engines": "google,duckduckgo,bing"
        }

        try:
            response = request.get(searxng_url, params=params, timeout=10)
            response.raise_for_status()
            results = response.json().get('results', [])

            if not results:
                dispatcher.utter_message(
                    text="No results found for your query.")
            else:
                dispatcher.utter_message(
                    text=f"Top Result: {results[0]['title']} - {results[0]['url']}")

        except requests.RequestException as e:
          dispatcher.utter_message(text="Error connecting to the search service")

        return []


class ActionRefineQuery(Action):
    def __init__(self):
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            "google/flan-t5-base")
        self.tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")

    def name(self) -> str:
        return "action_refine_query"

    def run(self, dispatcher, tracker, domain):
        user_query = tracker.latest_message.get("text")
        input_ids = self.tokenizer.encode(user_query, return_tensors="pt")
        outputs = self.model.generate(
            input_ids, max_length=50, num_beams=5, early_stopping=True)
        refined_query = self.tokenizer.decode(
            outputs[0], skip_special_tokens=True)

        dispatcher.utter_message(text="Refined Query: {refined_query}")
        return []


class ActionQueryMySQL(Action):
    def name(self):
         return "action_query_mysql"

    def run(self, dispatcher, tracker, domain):
      requested_table = tracker.get_slot('requested_table')
      db_host = os.getenv("DB_HOST")
      db_port = os.getenv("DB_PORT", 3306)
      db_database = os.getenv("DB_NAME")
      db_user = os.getenv("DB_USER")
      db_password = os.getenv("DB_PASSWORD")
      response = ""
      connection = None

      try:
           connection = mysql.connector.connect(
              host=db_host,
              database=db_database,
              user=db_user,
              password=db_password,
              port=db_port
           )
           if connection.is_connected():
             cursor = connection.cursor()
             query = "empty"

             if requested_table:
                 print("bug1")
                 if requested_table.lower() == "business":
                    query = "SELECT * FROM Business_School_Requirements"
                    print("bug2")
                 elif requested_table.lower() == "information technology":
                    query = "SELECT * FROM Information_Technology"
                    print("bug3")
                 else:
                     print("bug4")
                     response = "Unable to process table request"
                     dispatcher.utter_message(text=response)
                     return []
             else:
               print("issue with the requested_table")
             
             print("Query: " + query)
             cursor.execute(query)
             result = cursor.fetchall()
             print(f"query result: {result}")
             dispatcher.utter_message(text=str(result))
             if result:
               response = f"Here are the records I found: \n\n{result}"
               dispatcher.utter_message(text=str(response))
               return [SlotSet("records_found", True)]
             else:
               response = "Sorry, I couldn't find any matching records."
               return [SlotSet("records_found", False)]
               dispatcher.utter_message(text=response)
               cursor.close()
      except Error as e:
         reponse = f"Error while connecting to MySQL: {str(e)}"
         dispatcher.utter_message(text=response)
      finally:
        if connection.is_connected():
           cursor.close()
           connection.close()
      return []

    class ActionFallBack(Action):
        def name(self) -> str:
            return "action_fallback"

        def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
            dispatcher.utter_message(
                text = "I'm sorry, I didn't understand that. Could you rephrase?")
            return []
