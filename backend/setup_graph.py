from langchain_core.messages import HumanMessage, AIMessage, AnyMessage
from langgraph.graph.message import add_messages
from langgraph.graph import END
from typing import Literal, Annotated, List, Dict, Any
from pydantic import BaseModel, Field
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
# from IPython.display import Image, display
from langchain_core.runnables.graph import MermaidDrawMethod
from langchain_core.runnables import Runnable
from langgraph.graph import START, StateGraph
from datetime import datetime
import re
import os
import traceback
import warnings
warnings.filterwarnings('ignore', message='Could not download mistral tokenizer')
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from embedding import select_top_n_similar_documents
from create_db import create_documents, save_documents
from list import longlist
from mcp_bridge import weather_summary_sync, route_between_sync, versailles_itinerary_sync, multi_route_sync
import json
from pathlib import Path


# Load RAG docs with embeddings (preferred)
RAG_DOCS: list[dict[str, Any]] = []
for _candidate_path in [
    Path(__file__).parent / "data" / "tips_embedded.json",
    Path(__file__).parent.parent / "data" / "tips_embedded.json",
]:
    if _candidate_path.exists():
        try:
            with open(_candidate_path, "r", encoding="utf-8") as _fh:
                RAG_DOCS = json.load(_fh)
            break
        except Exception:
            # Fallback handled later if file is unreadable
            RAG_DOCS = []


def _parse_start_hour(s: str | None) -> tuple[int, int]:
    if not s:
        return 9, 0
    try:
        s2 = s.lower().replace("h", ":").replace(" ", "")
        hh, mm = (s2.split(":", 1) + ["00"])[:2]
        h = max(0, min(23, int(hh)))
        m = max(0, min(59, int(mm)))
        return h, m
    except Exception:
        return 9, 0


def _add_minutes(h: int, m: int, delta: int) -> str:
    total = (h * 60 + m + delta) % (24 * 60)
    return f"{total // 60:02d}:{total % 60:02d}"


def _build_default_plan(ni: dict[str, Any]) -> dict[str, Any]:
    h, m = _parse_start_hour(ni.get("hour"))

    timeline = [
        {"t": _add_minutes(h, m, 0), "title": "Latone → Fontaine d'Apollon", "note": "Photos tôt et moins d'affluence"},
        {"t": _add_minutes(h, m, 45), "title": "Promenade Grand Canal", "note": "Pause café au bord de l'eau"},
        {"t": _add_minutes(h, m, 90), "title": "Aller à l'entrée du Château", "note": "Contrôle billets et sécurité"},
        {"t": _add_minutes(h, m, 120), "title": "Galerie des Glaces", "note": "Fenêtre plus calme vers 14:30–15:30"},
    ]

    places = [
        "Bassin de Latone, Château de Versailles",
        "Bassin d'Apollon, Château de Versailles",
        "Grand Canal, Château de Versailles",
        "Entrée A Château de Versailles",
        "Galerie des Glaces, Château de Versailles",
    ]

    waypoints, geometry = [], None
    try:
        route = multi_route_sync(places=places, profile="walking")
        for wp in route.get("waypoints") or []:
            if not wp:
                continue
            name = wp.get("name") or wp.get("display_name") or "Étape"
            lat = wp.get("lat") or (wp.get("location", {}).get("lat") if isinstance(wp.get("location"), dict) else None)
            lon = wp.get("lon") or (wp.get("location", {}).get("lon") if isinstance(wp.get("location"), dict) else None)
            if lat is not None and lon is not None:
                waypoints.append({"name": name, "lat": lat, "lon": lon})
        geometry = route.get("geometry")
    except Exception:
        pass

    return {"title": "Suggested plan", "timeline": timeline, "waypoints": waypoints, "geometry": geometry}


def _to_plain_text(s: str) -> str:
    """Déballe du JSON éventuel et renvoie uniquement du texte pour le chat."""
    if not isinstance(s, str):
        s = str(s)
    s = s.strip()
    if not s:
        return s
    # 1) Enlever préfixes fréquents ("json", fences ```json, etc.)
    low = s.lower()
    if low.startswith("json"):
        brace = s.find("{")
        if brace != -1:
            s = s[brace:]
            low = s.lower()
    if low.startswith("```"):
        s = s.strip("`").strip()
    # 2) Parser si ça ressemble à du JSON
    candidate = s.lstrip()
    if candidate.startswith(('{', '[')):
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict) and isinstance(obj.get("response"), str):
                return obj["response"].strip()
            return json.dumps(obj, ensure_ascii=False, indent=2)
        except Exception:
            pass
    # 3) Dernier recours: extraire le premier bloc {...}
    match = re.search(r"\{.*?\}", s, re.S)
    if match:
        fragment = match.group(0)
        try:
            obj = json.loads(fragment)
            if isinstance(obj, dict) and isinstance(obj.get("response"), str):
                return obj["response"].strip()
            return json.dumps(obj, ensure_ascii=False, indent=2)
        except Exception:
            pass
    return s


def _strip_markdownish(s: str) -> str:
    s = s.replace("**", "").replace("__", "").replace("`", "")
    s = re.sub(r"^#{1,6}\s*", "", s, flags=re.MULTILINE)
    s = re.sub(r"^\s*[-*]\s+", "", s, flags=re.MULTILINE)
    s = re.sub(r"^\s*\d+\.\s+", "", s, flags=re.MULTILINE)
    s = re.sub(r"```.*?```", "", s, flags=re.DOTALL)
    return s.strip()


def to_plain_text(s: str) -> str:
    return _strip_markdownish(_to_plain_text(s))


def format_itinerary_response(text: str) -> str:
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text

    itinerary = payload.get("itinéraire") or payload.get("itinerary") or payload
    if not isinstance(itinerary, dict):
        return text

    parts: list[str] = []
    hdr = []
    if itinerary.get("date"):
        hdr.append(f"Date: {itinerary['date']}")
    sh = itinerary.get("heure_de_début") or itinerary.get("heure")
    if sh:
        hdr.append(f"Début: {sh}")
    if itinerary.get("type_de_visite"):
        hdr.append(f"Type: {itinerary['type_de_visite']}")
    if itinerary.get("budget"):
        hdr.append(f"Budget: {itinerary['budget']}")
    if hdr:
        parts.append(" | ".join(hdr))

    if itinerary.get("météo") or itinerary.get("meteo"):
        parts.append(f"Météo: {itinerary.get('météo') or itinerary.get('meteo')}")

    prog = itinerary.get("programme")
    if isinstance(prog, list) and prog:
        for slot in prog:
            if isinstance(slot, dict):
                time_range = slot.get("heure") or slot.get("time") or ""
                activity = slot.get("activité") or slot.get("activity") or ""
                details = slot.get("détails") or slot.get("details") or ""
                budget_slot = slot.get("budget") or ""
                advice = slot.get("conseil") or slot.get("tip") or ""
                line = " ".join(x for x in [time_range, "-", activity] if x).strip()
                extra = " ".join(x for x in [details, budget_slot, advice] if x).strip()
                parts.append(line if not extra else f"{line}. {extra}")

    tot = itinerary.get("budget_total_estimé") or itinerary.get("budget_total")
    if tot:
        parts.append(f"Budget estimé: {tot}")

    tips = itinerary.get("conseils_généraux") or itinerary.get("conseils")
    if isinstance(tips, list) and tips:
        parts.extend(tips)

    return "\n".join(p for p in parts if p).strip()

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
    itinerary_ready: bool = False
    route_payload: Dict | None = None
    plan_payload: Dict | None = None

class LLMManager():
    def __init__(self):
        self.llm = ChatMistralAI(model=MISTRAL_MODEL, temperature=0)

    def structured_invoke(self, prompt: ChatPromptTemplate, output_model: type[BaseModel], **kwargs) -> str:
        structured_llm = self.llm.with_structured_output(output_model)
        messages = prompt.format_messages(**kwargs)
        response = structured_llm.invoke(messages)
        return response

    def text_invoke(self, prompt: ChatPromptTemplate, **kwargs) -> str:
        messages = prompt.format_messages(**kwargs)
        result = self.llm.invoke(messages)
        return getattr(result, 'content', str(result))

class IntentOutput(BaseModel):
    """Modèle pour la sortie de l'agent d'intention"""
    user_wants_road_in_versailles: bool = Field(description="L'utilisateur veut visiter le château")
    user_wants_specific_info: bool = Field(description="L'utilisateur veut des informations spécifiques")
    user_asks_off_topic: bool = Field(description="L'utilisateur pose une question hors sujet")

class IntentAgent():
    def __init__(self):
        self.llm = LLMManager()

    def get_user_intent(self, state: State) -> IntentOutput:
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
            CRITICAL : Be really careful to ALWAYS return a valid JSON object with the exact fields and types specified above.

            """), ("human"," ===Messages: {messages}")])

        response = self.llm.structured_invoke(prompt, IntentOutput, messages=state.messages)
        return {
            "user_wants_road_in_versailles": response.user_wants_road_in_versailles,
            "user_wants_specific_info": response.user_wants_specific_info,
            "user_asks_off_topic": response.user_asks_off_topic,
        }

class OffTopicAgent():
    def __init__(self):
        self.llm = LLMManager()
    
    def get_necessary_info(self, state: State) -> Dict[str, Any]:
        extract_prompt = ChatPromptTemplate.from_messages([
            ('system', """Tu es un extracteur. Ta tâche: dire si l'utilisateur demande la MÉTÉO
            (éventuellement pour Versailles) et extraire: date (YYYY-MM-DD), heure, durée (texte), lieu.
            Réponds en JSON strict:
            {"is_weather": bool, "date": str|null, "hour": str|null, "duration_text": str|null, "place": str|null}"""),
            ('human', "Messages: {messages}\nRéponse JSON stricte:")
        ])
        ext: WeatherExtraction = self.llm.structured_invoke(extract_prompt, WeatherExtraction, messages=state.messages)

        if ext.is_weather:
            try:
                w = weather_summary_sync(
                    date=ext.date or datetime.today().strftime("%Y-%m-%d"),
                    start_time=ext.hour or "10:00",
                    duration_text=ext.duration_text or "180 min",
                    place=ext.place or "Château de Versailles, France",
                    lang="fr",
                )
                win, summ, hourly = w.get("window", {}), w.get("summary", {}), w.get("hourly", []) or []
                label = summ.get("label", "")
                advice = summ.get("advice", "")
                preview = []
                for h in hourly[:3]:
                    ts = (h.get("ts") or "")[11:16]
                    t = h.get("temp_c")
                    pr = h.get("precip_prob")
                    pm = h.get("precip_mm")
                    preview.append(f"{ts}: {t}°C, pluie {pr}% ({pm} mm)")
                preview_text = f"\nHeures clés: " + " · ".join(preview) if preview else ""
                msg = (f"Météo le {win.get('date')} {win.get('start')}-{win.get('end')} à {win.get('place')}: "
                       f"**{label}**. {advice}{preview_text}")
                return {"messages": AIMessage(content=msg)}
            except Exception:
                return {"messages": AIMessage(content="Je n'ai pas pu récupérer la météo maintenant. Souhaitez-vous que je propose un itinéraire tout de suite ?")}

        prompt = ChatPromptTemplate.from_messages([
            ('system', """Vous êtes Concierge Versailles. Traitez uniquement les sujets liés à Versailles (château, jardins, accès,
            météo locale, trajets). Salutations: répondez cordialement et invitez à préciser la demande. Pour la météo, utilisez l’API;
            en cas d’échec, donnez une alternative utile. Ne mentionnez pas d'erreurs techniques.
            Répondez en TEXTE SIMPLE UNIQUEMENT : pas de JSON, pas de Markdown, pas de blocs de code.
            Mettez la réponse destinée à l’utilisateur dans le champ `response` (texte pur)."""),
            ('human', "===Messages: {messages}  \n\n ===Répondez dans la langue de l'utilisateur : ")
        ])
        try:
            response = self.llm.structured_invoke(prompt, SpecificInfoOutput, messages=state.messages)
            text = _to_plain_text(response.response)
        except Exception:
            text = "Je peux vous aider pour Versailles : visites, accès, météo locale ou conseils pratiques." \
                   " N'hésitez pas à préciser votre besoin."
        return {"messages": AIMessage(content=text)}

class SpecificInfoOutput(BaseModel):
    """Modèle pour la sortie de l'agent d'information spécifique"""
    response: str = Field(description="Réponse à la question spécifique sur le château de Versailles")


class WeatherExtraction(BaseModel):
    is_weather: bool = Field(description="True if user asks about weather for a place/time")
    date: str | None = None
    hour: str | None = None
    duration_text: str | None = None
    place: str | None = None


class RouteExtraction(BaseModel):
    is_route: bool = Field(description="True if the user asks for directions or travel time")
    origin: str | None = None
    destination: str | None = None
    profile: Literal["walking", "driving", "cycling"] | None = None

class SpecificInfoAgent():
    def __init__(self):
        self.llm = LLMManager()
    
    def get_necessary_info(self, state: State) -> Dict[str, Any]:
        # First: detect route/directions requests
        route_prompt = ChatPromptTemplate.from_messages([
            ('system', """Tu es un extracteur. Dis si l'utilisateur demande un ITINÉRAIRE ou un TEMPS DE TRAJET
            entre deux lieux (y compris vers le Château de Versailles). Exemples FR: "comment aller",
            "itinéraire", "trajet", "combien de temps à pied", "distance", "à vélo", etc.
            Réponds en JSON strict:
            {"is_route": bool, "origin": str|null, "destination": str|null, "profile": "walking"|"driving"|"cycling"|null}
            Si le profil n'est pas explicite ("à pied", "en voiture", "à vélo"), laisse null."""),
            ('human', "Messages: {messages}\nRéponse JSON stricte:")
        ])
        ext: RouteExtraction = self.llm.structured_invoke(route_prompt, RouteExtraction, messages=state.messages)

        if ext.is_route:
            try:
                profile = ext.profile or "walking"
                if not ext.destination or "versailles" in (ext.destination or "").lower():
                    if not ext.origin:
                        ext.origin = "Gare de Versailles Château Rive Gauche"
                    res = versailles_itinerary_sync(origin=ext.origin, profile=profile)
                else:
                    origin = ext.origin or "Château de Versailles, France"
                    res = route_between_sync(origin=origin, destination=ext.destination, profile=profile)

                km = res.get("distance_km_approx")
                mins = res.get("duration_min_approx")
                src = res.get("source", {}).get("provider", "osrm")
                steps = res.get("steps", [])[:10]

                lines = []
                for step in steps:
                    road = step.get("road") or ""
                    modifier = step.get("modifier")
                    stype = step.get("type") or "step"
                    dist = step.get("distance_m")
                    label = f"- {stype}"
                    if modifier:
                        label += f" ({modifier})"
                    if road:
                        label += f" — {road}"
                    if dist is not None:
                        label += f" [{dist} m]"
                    lines.append(label)

                msg = (
                    f"**Itinéraire ({profile})**\n"
                    f"Distance ≈ {km} km · Durée ≈ {mins} min (source: {src})\n\n"
                    f"**Étapes clés**:\n" + ("\n".join(lines) if lines else "Instructions non disponibles.")
                )
                route_payload = {
                    "origin": res.get("origin"),
                    "destination": res.get("destination"),
                    "geometry": res.get("geometry"),
                    "steps": res.get("steps"),
                    "profile": res.get("profile", profile),
                    "distance_m": res.get("distance_m"),
                    "duration_s": res.get("duration_s"),
                    "source": res.get("source"),
                }
                return {"messages": AIMessage(content=msg), "route_payload": route_payload}
            except Exception as e:
                return {"messages": AIMessage(content=f"Désolé, l'itinéraire n'a pas pu être calculé ({e}).")}

        # Otherwise: normal specific-information flow
        prompt = ChatPromptTemplate.from_messages([
            ('system', """Vous êtes Concierge Versailles. Répondez aux questions spécifiques (œuvres, horaires, accès, restaurants à proximité, etc.).
            Si restaurants: proposez 2–3 options proches avec type de cuisine, fourchette de prix, distance approximative,
            et note « horaires à vérifier ». Si un détail est incertain, donnez la meilleure estimation et mentionnez qu’elle peut varier.
            Répondez en TEXTE SIMPLE UNIQUEMENT : pas de JSON, pas de Markdown, pas de blocs de code.
            Placez la réponse dans `response` (texte pur, concis)."""),
            ('human', "===Messages: {messages}  \n\n ===Répondez dans la langue de l'utilisateur : ")
        ])

        response = self.llm.structured_invoke(prompt, SpecificInfoOutput, messages=state.messages)
        return {"messages": AIMessage(content=_to_plain_text(response.response))}

class NecessaryInfoForRoad(BaseModel):
    """Modèle pour les informations nécessaires à l'itinéraire"""
    date: str | None = Field(default=None, description="Date de la visite")
    hour: str | None = Field(default=None, description="Heure de la visite")
    group_type: str | None = Field(default=None, description="Type de groupe (famille, amis, solo...)")
    time_of_visit: str | None = Field(default=None, description="Durée de la visite")
    budget: str | None = Field(default=None, description="Budget de la visite")

class ItineraryInfoOutput(BaseModel):
    """Modèle pour la sortie de l'agent d'informations d'itinéraire"""
    response: str = Field(description="La question ou réponse à l'utilisateur")
    necessary_info_for_road: NecessaryInfoForRoad = Field(description="Les informations collectées")
    is_complete: bool = Field(description="Vrai lorsque suffisamment d'informations ont été recueillies pour rédiger l'itinéraire")

class ItineraryInfoAgent():
    def __init__(self):
        self.llm = LLMManager()
    
    def get_necessary_info(self, state: State) -> Dict[str, Any]:
        prompt = ChatPromptTemplate.from_messages([
            ('system', """Vous êtes Concierge Versailles. Votre but est d’obtenir le minimum d’infos pour lancer un itinéraire faisable.
            Champs à remplir (priorité) : date, heure de début, durée (demi-journée/journée), type de groupe, budget.
            Règles : une question à la fois, réponses courtes; ne répétez pas tout l’état à chaque tour.
            Dès que vous avez (date + heure + durée) ET (groupe OU budget), mettez is_complete=true.
            Si l’utilisateur refuse un champ, laissez-le à null et mettez is_complete=true si l’essentiel est là.
            Si l’utilisateur dit « propose un itinéraire » ou demande un resto, considérez que l’information est suffisante.
            Répondez en TEXTE SIMPLE UNIQUEMENT (phrases courtes, pas de Markdown/JSON/emoji/listes).
            Mettez la réponse destinée à l’utilisateur dans `response` (texte pur)."""),
            ('human', "===Messages: {messages}  \n\n ===Répondez dans la langue de l'utilisateur (court et amical) : ")
        ])
        
        try:
            response = self.llm.structured_invoke(prompt, ItineraryInfoOutput, messages=state.messages, necessary_info_for_road=state.necessary_info_for_road, current_date=datetime.today().strftime('%Y-%m-%d'))
            text = _to_plain_text(response.response)
            info = response.necessary_info_for_road.model_dump()
            ready = response.is_complete
        except Exception:
            info = dict(state.necessary_info_for_road)
            ready = False
            text = "Je note : date, heure et durée de votre visite. Dites-moi simplement votre heure d’arrivée et si vous préférez jardins ou Trianon." \
                   " Nous pourrons ensuite bâtir un itinéraire."
        return {
            "necessary_info_for_road": info,
            "itinerary_ready": ready,
            "messages": AIMessage(content=text),
        }

class ItineraryInfoOutputEval(BaseModel):
    """Modèle pour la sortie de l'agent d'informations d'itinéraire en évaluation"""
    necessary_info_for_road: NecessaryInfoForRoad = Field(description="Les informations collectées")

class ItineraryInfoAgentEval():
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
              
            Today, the date is {current_date}, so if the user says "today" or "this weekend",
            interpret it accordingly.
            When you ask for the hours, precise the opening hours.
            The user can response "10h", "10h00", "10:00", "10:00am", "10:00 am", "10 am", "10am" for 10 o'clock.
            
            If you have any doubt regarding the user answers, set the field to null.
            
            Your response must be a JSON object (without markdown code blocks or any other formatting) with the following fields:
            {{ "necessary_info_for_road": {{date: str | null, hour: str | null, group_type: str | null, 
              time_of_visit: str | null, budget: str | null}}
            }}
            CRITICAL : Be really careful to ALWAYS return a valid JSON object with the exact fields and types specified above.
            """), ("human"," ===Messages: {messages}  \n\n ===Your answer in the user's language : ")])
        
        response = self.llm.structured_invoke(prompt, ItineraryInfoOutputEval, messages=state.messages, necessary_info_for_road=state.necessary_info_for_road, current_date=datetime.today().strftime('%Y-%m-%d'))
        return {
            "necessary_info_for_road": response.necessary_info_for_road.model_dump()
        }

class RoadOutput(BaseModel):
    """Modèle pour la sortie de l'agent de création d'itinéraire"""
    response: str = Field(description="L'itinéraire détaillé pour l'utilisateur")

class RoadInVersaillesAgent():
    def __init__(self):
        self.llm = LLMManager()
    
    def get_necessary_info(self, state: State) -> Dict[str, Any]:
        prompt = ChatPromptTemplate.from_messages(
            [('system', """You are an expert assistant for visits to the Château de Versailles.
Return a concise, user-ready answer in PLAIN TEXT ONLY:
- no JSON
- no Markdown (no **, #, lists, code fences)
- no emojis
Write short paragraphs separated by newlines.

Use:
- date/hour/group/time/budget from {necessary_info_for_road}
- RAG context: {rag_context}
- weather context (if provided): {weather_context}"""),
             ("human","Messages: {messages}\n\nAnswer in the user's language, plain text: ")]
        )

        query_client = ("Le client veut visiter le château de Versailles le {date} à {hour} avec un groupe de type {group_type}. "
                        "Il prévoit de visiter pendant {time_of_visit} heures et son budget est {budget}.").format(**state.necessary_info_for_road)
        if RAG_DOCS:
            rag_context = select_top_n_similar_documents(
                query_client,
                documents=RAG_DOCS,
                n=50,
                metric='euclidian',
            )
            data_parts: list[str] = []
            for doc in rag_context:
                if isinstance(doc, dict):
                    data_parts.append(doc.get("texte") or doc.get("content") or "")
                else:
                    data_parts.append(str(doc))
            data = ", ".join(part for part in data_parts if part)
        else:
            data = ", ".join(
                doc.get("texte") if isinstance(doc, dict) else str(doc)
                for doc in longlist[:50]
            )

        ni = state.necessary_info_for_road
        weather_context = ""
        try:
            if ni.get('date') and ni.get('hour') and ni.get('time_of_visit'):
                w = weather_summary_sync(
                    date=ni['date'],
                    start_time=ni['hour'],
                    duration_text=ni['time_of_visit'],
                    place="Château de Versailles, France",
                    lang="fr",
                )
                win, summ = w.get("window", {}), w.get("summary", {})
                weather_context = (f"Météo {win.get('date')} {win.get('start')}-{win.get('end')} à {win.get('place')}: "
                                   f"{summ.get('label')} — {summ.get('advice')}.")
        except Exception:
            weather_context = ""

        resp: RoadOutput = self.llm.structured_invoke(
            prompt,
            RoadOutput,
            messages=state.messages,
            necessary_info_for_road=state.necessary_info_for_road,
            rag_context=data,
            weather_context=weather_context,
            date=state.necessary_info_for_road.get('date'),
            hour=state.necessary_info_for_road.get('hour')
        )
        final_text = (resp.response or "").strip()
        plan = _build_default_plan(state.necessary_info_for_road)
        return {
            "messages": AIMessage(content=final_text),
            "itinerary_ready": False,
            "plan_payload": plan,
        }
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

        # Fast-path keywords to trigger itinerary immediately
        try:
            last = (state.messages[-1].content or "").lower()
        except Exception:
            last = ""
        fast = any(k in last for k in ("itinéraire", "itinéaire", "plan", "programme", "resto", "restaurant"))

        if state.itinerary_ready or all_fields_filled or fast:
            return "road_in_versailles_agent"
        else:
            return END
        
    @staticmethod
    def route_intent_node_eval(
        state: State,
    ) -> Literal["itinerary_info_agent_eval", "off_topic_agent", "specific_info_agent", END]:

        if state.user_wants_road_in_versailles:
            return "itinerary_info_agent_eval"
        elif state.user_asks_off_topic :
            return "off_topic_agent"
        elif state.user_wants_specific_info :
            return "specific_info_agent"
        else:
            return END
    @staticmethod
    def route_road_pre_agent_eval(
        state: State,
    ) -> Literal["road_in_versailles_agent", END]:
        """Route from ItineraryInfoAgent to RoadInVersaillesAgent only if all necessary info is filled."""
        return "road_in_versailles_agent"

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
        
        # Méthode 1 : Sauvegarder le code Mermaid (toujours fonctionne)
        mermaid_code = runnable.get_graph().draw_mermaid()
        
        # Sauvegarder dans un fichier
        with open("graph.mmd", "w") as f:
            f.write(mermaid_code)
        
        print("✅ Graphe Mermaid sauvegardé dans 'graph.mmd'")
        print("📊 Pour visualiser :")
        print("   - Ouvrez https://mermaid.live/")
        print("   - Collez le contenu de graph.mmd")
        print("   - Ou utilisez l'extension VSCode 'Markdown Preview Mermaid Support'")
        
        # Méthode 2 : Créer un fichier HTML pour visualisation locale
        html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                <script>mermaid.initialize({{ startOnLoad: true }});</script>
            </head>
            <body>
                <div class="mermaid">
            {mermaid_code}
                </div>
            </body>
            </html>
            """
        with open("graph.html", "w") as f:
            f.write(html_content)
        
        print("✅ Fichier HTML sauvegardé dans 'graph.html'")
        print("🌐 Ouvrez 'graph.html' dans votre navigateur pour voir le graphe")
        
        return mermaid_code

class GraphManagerEval():
    def __init__(self):
        self.agent = IntentAgent()
        self.itineraryInfoAgent = ItineraryInfoAgentEval()
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
            "itinerary_info_agent_eval",
            self.itineraryInfoAgent.get_necessary_info,
            description="Get necessary info for visiting the gardens of Versailles",
        )

        graph.add_node(
            "road_in_versailles_agent",
            self.roadInVersaillesAgent.get_necessary_info,
            description="Create itinerary for visiting Versailles",
        )

        graph.add_conditional_edges(
                    "intent_node", self.conditions.route_intent_node_eval)

        graph.add_conditional_edges(
                    "itinerary_info_agent_eval", self.conditions.route_road_pre_agent_eval)

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
        
        # Méthode 1 : Sauvegarder le code Mermaid (toujours fonctionne)
        mermaid_code = runnable.get_graph().draw_mermaid()
        
        # Sauvegarder dans un fichier
        with open("graph.mmd", "w") as f:
            f.write(mermaid_code)
        
        print("✅ Graphe Mermaid sauvegardé dans 'graph.mmd'")
        print("📊 Pour visualiser :")
        print("   - Ouvrez https://mermaid.live/")
        print("   - Collez le contenu de graph.mmd")
        print("   - Ou utilisez l'extension VSCode 'Markdown Preview Mermaid Support'")
        
        # Méthode 2 : Créer un fichier HTML pour visualisation locale
        html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                <script>mermaid.initialize({{ startOnLoad: true }});</script>
            </head>
            <body>
                <div class="mermaid">
            {mermaid_code}
                </div>
            </body>
            </html>
            """
        with open("graph.html", "w") as f:
            f.write(html_content)
        
        print("✅ Fichier HTML sauvegardé dans 'graph.html'")
        print("🌐 Ouvrez 'graph.html' dans votre navigateur pour voir le graphe")
        
        return mermaid_code
    
from langchain_core.messages import HumanMessage

def talk_to_agent(state, mgr, query=None):
    query = input("You: ") if query is None else query
    state.messages+=[HumanMessage(content = query)]
    class ChatAgentOutput(BaseModel):
        response: str
        route: Dict | None = None
        plan: Dict | None = None
    try:
        response = mgr.run_agent(state)
    except Exception as exc:
        traceback.print_exc()
        state.route_payload = None
        error_text = f"Erreur interne ({exc.__class__.__name__}: {exc})"
        return ChatAgentOutput(response=error_text, route=None)
    # Update state while preserving messages
    for key, value in response.items():
        if key != 'messages':
            setattr(state, key, value)
        else:
            state.messages = value
    last = state.messages[-1].content
    safe = _to_plain_text(last)
    pretty = format_itinerary_response(safe)
    final_text = to_plain_text(pretty or safe)
    print("Agent:", final_text)
    payload = state.route_payload
    payload_plan = state.plan_payload
    # reset one-shot payload to avoid re-sending on next turns
    state.route_payload = None
    state.plan_payload = None
    return ChatAgentOutput(response=final_text, route=payload, plan=payload_plan)

if __name__ == "__main__":
    state = State()
    mgr = GraphManagerEval()
    print(INIT_MESSAGE)
    while True:
        print(talk_to_agent(state, mgr))
