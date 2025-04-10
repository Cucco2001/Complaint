
from generator import generate_complaint, filter_relevant_articles
import json

# Simuliamo 5 articoli (alcuni rilevanti, altri no)
sample_articles = [
    {"title": "55) SAFETY CAR", "content": "Drivers must not drive erratically while the safety car is deployed..."},
    {"title": "54) INCIDENTS DURING THE RACE", "content": "Unless it is clear to the stewards that a driver was wholly or predominantly to blame..."},
    {"title": "18) SANCTIONS", "content": "The stewards may impose penalties including reprimands and fines..."},
    {"title": "49) FORMATION LAP", "content": "Formation lap procedure when starting behind the safety car..."},
    {"title": "1) REGULATIONS", "content": "The FIA will organise the Formula One Championship..."}
]

# Caso test complesso: guida irregolare sotto safety car
penalty_type = "Drive-through penalty for driving erratically behind the Safety Car and failing to respect the Safety Car delta time"
race_conditions = "During Lap 14, while under Safety Car conditions, the driver reduced speed in a straight to warm tyres and brakes, resulting in a momentary fluctuation in delta time. No sector-wide delta was violated."

# Fase 1: test del filtro
filtered = filter_relevant_articles(sample_articles, penalty_type, race_conditions)

print("\n🧠 ARTICOLI SELEZIONATI DA GPT (score >= 2):")
for art in filtered:
    print(f"- {art['title']}")

# Fase 2: generazione completa
print("\n✍️ COMPLAINT GENERATO:")
complaint = generate_complaint(sample_articles, penalty_type, race_conditions, driver="Carlos Sainz", lap=14, turn="T5-T6")
print(complaint)
