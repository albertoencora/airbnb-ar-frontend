from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
from dotenv import load_dotenv
from openai import OpenAI

from rag import load_property_data, build_context
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

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # solo desarrollo
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    property_id: Optional[str] = "demo_property"
    question: str
    language: Optional[str] = "es"

NO_INFO_MESSAGES = {
    "es": "No tengo esa información test, por favor consulta con el encargado.",
    "en": "I don't have that information. Please contact the host."
}

@app.post("/ask")



def ask(req: AskRequest):
    lang = (req.language or "es").lower()
    lang_key = "en" if lang.startswith("en") else "es"
    try:
        # 1) Cargar entidad
        entity = load_property_data(req.property_id)
        print("DEBUG entity type:", type(entity))
        print("DEBUG entity value:", entity)
        # 2) Contexto desde entidad
        context_text = build_context(entity)

        # 3) Prompt universal
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            entity_name=entity.get("name", req.property_id),
            entity_type=entity.get("type", "generic"),
            language=req.language or "es",
           
            context=context_text
        )

        # 4) Recomendaciones dinámicas (opcional)
        intent = detect_intent(req.question)
        suggestions = RECOMMENDATIONS.get(intent, [])

        recommendation_text = ""
        if suggestions:
            recommendation_text = (
                "\nYou may suggest up to 2 local options from the list below, "
                "only if relevant and naturally:\n"
                + "\n".join(suggestions)
            )

        # 5) Llamada OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                # si quieres meter recomendaciones, puedes activar esto:
                # {"role": "system", "content": recommendation_text},
                {"role": "user", "content": req.question}
            ],
            temperature=0.3
        )

        # ✅ Respuesta segura (evita null/None)
        answer = None

        if response.choices and response.choices[0].message:
            answer = response.choices[0].message.content

        #if not answer:
        #    answer = "No tengo esa información, por favor consulta con el encargado."
        LOW_QUALITY_PATTERNS = [
        "no tengo esa información",
        "no dispongo de esa información",
        "no cuento con esa información",
        "i don't have that information",
        "i do not have that information"
        ]
        answer_text = answer.lower()

        is_generic = any(p in answer_text for p in LOW_QUALITY_PATTERNS)
        if not answer or is_generic:
            answer = NO_INFO_MESSAGES.get(lang_key, NO_INFO_MESSAGES["es"])
        #if not answer:
        #     answer = NO_INFO_MESSAGES.get(lang_key, NO_INFO_MESSAGES["es"])

        return {"answer": answer,  
                "suggestions": entity.get("suggestions", {}).get("suggestions", {})}
    

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
