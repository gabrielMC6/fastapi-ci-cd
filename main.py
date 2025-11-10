from fastapi import FastAPI
import random

app = FastAPI()

curiosidades = [
    "O polvo tem três corações e o sangue azul.",
    "Abelhas conseguem reconhecer rostos humanos.",
    "A Torre Eiffel pode ficar até 15 cm mais alta no verão.",
    "Os golfinhos dormem com um olho aberto.",
    "O primeiro computador pesava mais de 27 toneladas.",
    "As vacas têm melhores amigas e ficam estressadas quando se separam.",
    "Bananas são naturalmente radioativas.",
    "Na Antártida existe uma cachoeira vermelha chamada Blood Falls.",
    "O barulho que ouvimos do mar em uma concha é, na verdade, o som do nosso próprio sangue.",
    "Os flamingos só ficam rosa por causa da alimentação."
]

@app.get("/")
async def root():
    return {"message": "API de Curiosidades pronta!"}

@app.get("/curiosidade")
async def get_curiosidade():
    return {"curiosidade": random.choice(curiosidades)}

@app.get("/health")
async def health():
    return {"status": "healthy"}
