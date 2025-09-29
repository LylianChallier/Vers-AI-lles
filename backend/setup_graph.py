from langchain_core.messages import HumanMessage, AIMessage, AnyMessage
from langgraph.graph.message import add_messages
from langgraph.graph import END
from typing import Literal, Annotated, List, Dict, Any
from pydantic import BaseModel, Field
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
#from IPython.display import Image, display
from langchain_core.runnables.graph import MermaidDrawMethod
from langchain_core.runnables import Runnable
from langgraph.graph import START, StateGraph
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

MISTRAL_MODEL = os.getenv('MISTRAL_MODEL', 'mistral-7b-instruct-v0.1')

INIT_MESSAGE = "Bonjour ! Je suis votre assistant virtuel pour organiser votre visite au château de Versailles. " \
"Je peux soit vous créer un itinéraire pour votre visite à partir de votre situation (visite en famille, " \
"budget économique, temps de visite...), ou bien vous informer plus en détail sur des détails dans le château.\n\n" \
"Si vous souhaitez commencer, dites-moi simplement que vous voulez visiter le château de Versailles " \
"ou que vous voulez des informations sur un aspect du château !"

def get_init_messages() -> list:
    return [AIMessage(content=INIT_MESSAGE)]

class State(BaseModel):
    messages: Annotated[List[AnyMessage], add_messages] = Field(default_factory=get_init_messages)
    user_wants_road_in_versailles : bool | None = None
    user_asks_off_topic : bool | None = None
    user_wants_specific_info : bool | None = None
    necessary_info_for_road : Dict = {"date": None, "hour": None, "group_type": None, "time_of_visit": None, "budget": None}

class LLMManager():
    def __init__(self):
        self.llm = ChatMistralAI(model=MISTRAL_MODEL, temperature=0)

    def invoke(self, prompt: ChatPromptTemplate, **kwargs) -> str:
      agent = self.llm
      messages = prompt.format_messages(**kwargs)
      response = agent.invoke(messages)
      return response.content


class IntentAgent():
    def __init__(self):
        self.llm = LLMManager()
    
    def get_user_intent(self, state: State) -> Dict[str, Any]:
        prompt = ChatPromptTemplate.from_messages(
            [('system', """You are an expert AI assistant that analyzes user messages to determine their
            intent and extract relevant information. Your role is to identify if the user :
              - wants to visit the castle in Versailles (set user_wants_road_in_versailles to true)
              - wants specific information about something in the castle of Versailles (set user_wants_specific_info to true)
              - is talking about something completely unrelated to Versailles castle (set user_asks_off_topic to true)

            Examples of requests related to visiting the castle of Versailles:
            - "I want to visit Versailles"
            - "How can I plan a trip to the castle?"

            Examples of requests related to specific information about the castle of Versailles:
            - "Tell me about the Hall of Mirrors"
            - "What are the opening hours of the gardens?"
            - "Who designed the fountains in the gardens?"
              
            Examples of off-topic requests:
            - "I want to visit the Tower of Pisa"
            - "Tell me about cooking pasta"
            - "What's the weather like?"
              
            Your response must be a JSON object (without markdown code blocks or any other formatting) with the following fields:
            {{ user_wants_road_in_versailles: bool,
                user_wants_specific_info: bool,
            user_asks_off_topic: bool
            }}
            
            IMPORTANT: Only ONE field can be true at a time. There has to be one true, the others has to be false.
            You cannot have all 3 fields false or all 3 fields true.

            """), ("human"," ===Messages: {messages}")])

        response = self.llm.invoke(prompt, messages = state.messages)
        output_parser = JsonOutputParser()
        parsed_response = output_parser.parse(response)

        return {
            "user_wants_road_in_versailles": parsed_response["user_wants_road_in_versailles"],
            "user_wants_specific_info": parsed_response["user_wants_specific_info"],
            "user_asks_off_topic": parsed_response["user_asks_off_topic"]
        }
class OffTopicAgent():
    def __init__(self):
        self.llm = LLMManager()
    
    def get_necessary_info(self, state: State) -> Dict[str, Any]:
        return {
        "messages": ["Désolé, je ne peux répondre qu'à des questions sur le château de Versailles..."]
    }

class SpecificInfoAgent():
    def __init__(self):
        self.llm = LLMManager()
    
    def get_necessary_info(self, state: State) -> Dict[str, Any]:
        prompt = ChatPromptTemplate.from_messages(
            [('system', """You are an expert AI assistant specialised in providing specific information about the 
            castle of Versailles based on user questions.
            Your role is to answer questions about the castle of Versailles using your knowledge.
            If you don't know the answer, respond with "Je ne sais pas".
            If the question is off-topic, respond with "Désolé, je ne peux répondre qu'à des questions sur le château de Versailles."
            
            Your response must be a JSON object (without markdown code blocks or any other formatting) with the following fields:
            {{ "response": str
            }}
            """), ("human"," ===Messages: {messages}  \n\n ===Your answer in the user's language : ")])
        
        response = self.llm.invoke(prompt, messages = state.messages)
        output_parser = JsonOutputParser()
        parsed_response = output_parser.parse(response)

        return {"messages": AIMessage(content=parsed_response["response"])}


class ItineraryInfoAgent():
    def __init__(self):
        self.llm = LLMManager()
    
    def get_necessary_info(self, state: State) -> Dict[str, Any]:
        prompt = ChatPromptTemplate.from_messages(
            [('system', """You are an expert AI assistant specialised in creating plans to visit to the 
            castle of Versailles based on different user situations.
            Your role is to identify what is needed to plan the perfect visit to the castle in Versailles 
            for the user and ask the required information found in the following dictionnary :
            {necessary_info_for_road}
            
            Using the information given by the user fill the dictionnary and ask a question 
            at a time starting by the dictionnary keys order.
              
            Ask for the real date if the user gives a relative date like "today" or "tomorrow" or something similar.
            When you ask for the hours, precise the opening hours.
            The user can response "10h", "10h00", "10:00", "10:00am", "10:00 am", "10 am", "10am" for 10 o'clock.
              
            If you have any doubt regarding the user answers, ask to clarify. Continue to ask questions 
            until all fields are filled. If the user doesn't want to give a specific information, answer him
            that your itinerary will be less precise. Ask again, if the user insists to not give the information,
            set it to null.
            If the user gives an answer that is not relevant to the question, ignore it and ask again the same question.
            
            Your response must be a JSON object (without markdown code blocks or any other formatting) with the following fields:
            {{ "response": str,
              "necessary_info_for_road": {{date: str | null, hour: str | null, group_type: str | null, 
              time_of_visit: str | null, budget: str | null}}
            }}
            """), ("human"," ===Messages: {messages}  \n\n ===Your answer in the user's language : ")])
        
        response = self.llm.invoke(prompt, messages = state.messages,
                                   necessary_info_for_road = state.necessary_info_for_road)
        output_parser = JsonOutputParser()
        parsed_response = output_parser.parse(response)

        return {"necessary_info_for_road" : parsed_response["necessary_info_for_road"],
                "messages": AIMessage(content=parsed_response["response"])}

class RoadInVersaillesAgent():
    def __init__(self):
        self.llm = LLMManager()
    
    def get_necessary_info(self, state: State) -> Dict[str, Any]:
        prompt = ChatPromptTemplate.from_messages(
            [('system', """You are an expert AI assistant specialised in organizing visits to the castle of Versailles.
            Your role is to create a plan a visit to the castle in Versailles based on the information written in the 
            following dictionnary :
            {necessary_info_for_road}
            If you have any doubt regarding the user answers, ask to clarify.
            
            To create the itinerary, consider the following:
            - The date and hour of the visit to suggest activities that are open at that time.
            - The type of group (family, friends, solo, etc.) to tailor the recommendations.
            - The time of visit to suggest activities that fit within that timeframe.
            - The budget to recommend activities that are affordable for the user.
                          
            Your response must be a JSON object (without markdown code blocks or any other formatting) with the following field:
            {{ "response": str
            }}
            """), ("human"," ===Messages: {messages}  \n\n ===Your answer in the user's language : ")])
        
        response = self.llm.invoke(prompt, messages = state.messages, necessary_info_for_road = state.necessary_info_for_road)
        output_parser = JsonOutputParser()
        parsed_response = output_parser.parse(response)

        return {"messages": AIMessage(content=parsed_response["response"])}

class Conditions():
    @staticmethod
    def route_intent_node(
        state: State,
    ) -> Literal["itinerary_info_agent", "off_topic_agent", "specific_info_agent", END]:

        if state.user_wants_road_in_versailles:
            return "itinerary_info_agent"
        elif state.user_asks_off_topic :
            return "off_topic_agent"
        elif state.user_wants_specific_info :
            return "specific_info_agent"
        else:
            return END

    @staticmethod
    def route_road_pre_agent(
        state: State,
    ) -> Literal["road_in_versailles_agent", END]:
        """Route from ItineraryInfoAgent to RoadInVersaillesAgent only if all necessary info is filled."""

        # Check if all fields in necessary_info_for_road are non-null
        all_fields_filled = all(
            value is not None
            for value in state.necessary_info_for_road.values()
        )

        if all_fields_filled:
            return "road_in_versailles_agent"
        else:
            return END
    
    # @staticmethod
    # def route_specific_info_agent(
    #     state: State,
    # ) -> Literal["specific_info_agent", END]:
    #     if state.user_wants_specific_info:
    #         return "specific_info_agent"
    #     else:
    #         return END

class GraphManager():
    def __init__(self):
        self.agent = IntentAgent()
        self.itineraryInfoAgent = ItineraryInfoAgent()
        self.offTopicAgent = OffTopicAgent()
        self.roadInVersaillesAgent = RoadInVersaillesAgent()
        self.specificInfoAgent = SpecificInfoAgent()
        self.conditions = Conditions()
    
    def create_workflow(self) -> StateGraph:
        graph = StateGraph(State)

        graph.add_node(
            "intent_node",
            self.agent.get_user_intent,
            description="Determine user intent from messages",
        )

        graph.add_node(
            "off_topic_agent",
            self.offTopicAgent.get_necessary_info,
            description="Handle off-topic questions",
        )

        graph.add_node(
            "specific_info_agent",
            self.specificInfoAgent.get_necessary_info,
            description="Get specific information about the gardens of Versailles",
        )

        graph.add_node(
            "itinerary_info_agent",
            self.itineraryInfoAgent.get_necessary_info,
            description="Get necessary info for visiting the gardens of Versailles",
        )

        graph.add_node(
            "road_in_versailles_agent",
            self.roadInVersaillesAgent.get_necessary_info,
            description="Create itinerary for visiting Versailles",
        )

        graph.add_conditional_edges(
                    "intent_node", self.conditions.route_intent_node)

        graph.add_conditional_edges(
                    "itinerary_info_agent", self.conditions.route_road_pre_agent)

        graph.add_edge(START, "intent_node")
        graph.add_edge("road_in_versailles_agent", END)
        graph.add_edge("off_topic_agent", END)
        graph.add_edge("specific_info_agent", END)

        return graph
    
    def return_graph(self) -> Runnable:
        return self.create_workflow().compile()
    
    def run_agent(self, state: State) -> State:
        """Run the agent workflow and return the formatted answer."""
        app: Runnable = self.create_workflow().compile()
        result: State = app.invoke(state)
        return result

    def display_image(self):
        runnable = self.return_graph()
        import nest_asyncio
        nest_asyncio.apply()
        display(
            Image(
                runnable.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.PYPPETEER)

            )
        )

from langchain_core.messages import HumanMessage
state : State = State()
mgr = GraphManager()
print("AI : ", INIT_MESSAGE)
while True:
    message = input("You: ")
    state.messages+=[HumanMessage(content = message)]

    response = mgr.run_agent(state)
    # Update state while preserving messages
    for key, value in response.items():
        if key != 'messages':
            setattr(state, key, value)
        else:
            state.messages = value

    print("AI : ", state.messages[-1].content)