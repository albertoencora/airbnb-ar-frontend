import json
import os
def build_context(data: dict) -> str:
    sections = []

    sections.append(f"Place name: {data.get('name')}")
    sections.append(f"Place type: {data.get('type')}")
    sections.append(f"Location: {data.get('location', {}).get('address')}")

    if "spaces" in data:
        sections.append("\nSpaces:")
        for s in data["spaces"]:
            sections.append(
                f"- {s['name']}: {s.get('description', '')}. "
                f"Rules: {', '.join(s.get('rules', []))}. "
                f"Availability: {s.get('availability', {}).get('from', '')} - {s.get('availability', {}).get('to', '')}"
            )

    if "services" in data:
        sections.append("\nServices:")
        for srv in data["services"]:
            sections.append(f"- {srv['name']}: {srv.get('details', '') or srv.get('how_to_request', '')}")

    if "rules" in data:
        sections.append("\nGeneral rules:")
        for rule in data["rules"]:
            sections.append(f"- {rule}")

    if "schedules" in data:
        sections.append("\nSchedules:")
        for k, v in data["schedules"].items():
            sections.append(f"- {k}: {v}")

    if "faqs" in data:
        sections.append("\nFAQs:")
        for f in data["faqs"]:
            sections.append(f"- Q: {f['question']} A: {f['answer']}")

    if "recommendations" in data:
        sections.append("\nExternal recommendations:")
        for k, items in data["recommendations"].items():
            sections.append(f"- {k}: {', '.join(items)}")

    return "\n".join(sections)


def load_property_data(property_id : str):
    with open(f"data/{property_id}.json", "r", encoding="utf-8") as f:
      return json.load(f)
    if not os.path.exists(path):
       raise FileNotFoundError(
           f"No existe el archivo de datos para la propiedad: {property_id}"
       )

    with open(path, "r", encoding="utf-8") as f:
       return json.load(f)

#def build_context(data):
#    return f"""
#Nombre: {data['name']}
#Reglas: {data['rules']}
#Check-in: {data['checkin']}
#Check-out: {data['checkout']}
#WiFi: {data['wifi']}
#Aire acondicionado: {data['air_conditioning']}
#Contacto: {data['contact']}
#"""
#print(dir())
