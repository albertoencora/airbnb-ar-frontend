from fastapi import FastAPI
from pydantic import BaseModel
from rag import load_property_data, build_context
#from prompts import AIRBNB_CONTEXT, SYSTEM_PROMPT
from prompts import SYSTEM_PROMPT_TEMPLATE

def detect_intent(question: str) -> str:
    q = question.lower()

    if any(word in q for word in ["comer", "restaurante", "cenar", "almorzar", "food"]):
        return "food"
    if any(word in q for word in ["tour", "excursion", "actividad", "paseo"]):
        return "tours"
    if any(word in q for word in ["carro", "auto", "rentar", "rent", "transport"]):
        return "transport"
    if any(word in q for word in ["tienda", "comprar", "shop"]):
        return "shopping"

    return "general"

import openai, os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body
from openai import OpenAI
from fastapi import HTTPException
from typing import Optional

RECOMMENDATIONS = {
    "food": [
        "Restaurante La Oveja – cocina local muy popular",
        "Surf & Turf – mariscos y carnes"
    ],
    "tours": [
        "Tamarindo Adventures – tours de canopy y rafting",
        "Pacific Sun Tours – excursiones de un día"
    ],
    "transport": [
        "Rent a Car Guanacaste – entrega en el alojamiento",
        "Eco Rent – opciones económicas"
    ],
    "shopping": [
        "Souvenir Market Tamarindo – artesanías locales",
        "Playa Shops – ropa y recuerdos"
    ]
}


OPENAI_MODEL = "gpt-4o-mini"

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # solo desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo de entrada
class AskRequest(BaseModel):
    property_id: Optional[str] = "demo_property"
    question: str
    language: Optional[str] = "es"
    
class Question(BaseModel):
    property_id: str
    question: str

@app.post("/ask")
def ask(req: AskRequest):
   
    data = load_property_data(req.property_id)
    context = build_context(data)
    
    language = req.language or "es"
    place_type = data.get("type", "generic")
   
    #seleccion de la api key
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(language=language,
        place_type=place_type)
    
    # 🔍 Detectar intención del huésped
    intent = detect_intent(req.question)
    suggestions = RECOMMENDATIONS.get(intent, [])

# 🧠 Texto dinámico de recomendaciones
    recommendation_text = ""
    if suggestions:
        recommendation_text = (
        "\nYou may suggest up to 2 local options from the list below, "
        "only if relevant and naturally:\n"
        + "\n".join(suggestions)
    )

    try:
     response = client.chat.completions.create(
        model= OPENAI_MODEL,
        
        messages=[
            {"role": "system", "content": system_prompt},
           # {"role": "system", "content": AIRBNB_CONTEXT},
            {"role": "system", "content": context},
            {"role": "system", "content": recommendation_text},
            {"role": "user", "content": req.question}
            #{"role": "user", "content": f"{context}\nPregunta: {req.question}"}
        ],
        temperature=0.3
    )

     return {"answer": response.choices[0].message.content}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

#@app.get("/")
#def root():
 #   return {"status": "backend funcionando"}

