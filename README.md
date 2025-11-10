CI/CD com o GitHub Actions – DevSecOps
Objetivo
Automatizar todo o ciclo de desenvolvimento, build e deploy de uma aplicação FastAPI, usando GitHub Actions, Docker Hub e ArgoCD em um ambiente Kubernetes local configurado com Rancher Desktop.
Pré-requisito

• Conta no GitHub (repositório público)
• Conta no Docker Hub com token de acesso
• Rancher Desktop com Kubernetes habilitado
• kubectl configurado corretamente (kubectl get nodes)
• ArgoCD instalado no cluster local
• Git instalado
• Python 3 e Docker instalados
  
  Etapa 1 – Criação da aplicação e repositórios

Foram criados dois repositórios públicos:

fastapi-ci-cd: contém a aplicação, Dockerfile, requirements.txt e workflow do GitHub Actions.

app-manifest: contém os arquivos de manifesto Kubernetes (deployment.yaml e service.yaml), monitorados pelo ArgoCD.

A aplicação FastAPI (main.py) possui dois endpoints simples:
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "jacare"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
Dependências no requirements.txt:
fastapi==0.104.1
uvicorn==0.24.0
Dockerfile:
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

Etapa 2 – Configuração do pipeline no GitHub Actions

Primeiro, foram configurados os Secrets no repositório fastapi-ci-cd:

DOCKER_USERNAME → usuário do Docker Hub

DOCKER_PASSWORD → token de acesso do Docker Hub

MANIFESTS_TOKEN → token de acesso para gravar no repositório app-manifest

Com os secrets definidos, foi criado o workflow .github/workflows/ci-cd.yaml para automatizar testes, build da imagem Docker, publicação no Docker Hub e atualização dos manifests.

O pipeline é acionado a cada push na branch main e dividido em três etapas principais:

Testar código: valida que a aplicação FastAPI pode ser importada e inicializada.

Build e push da imagem: gera a imagem Docker e publica no Docker Hub usando os secrets configurados.

Atualização dos manifests: acessa o repositório app-manifest e altera a tag da imagem no deployment.yaml, criando automaticamente um pull request com a nova versão.

Workflow comentado:

name: CI/CD Pipeline

permissions:
  contents: write       # permite atualizar conteúdo do repo
  pull-requests: write  # permite criar pull requests

on:
  push:
    branches: [ main ]  # dispara a cada push na branch principal

env:
  IMAGE_NAME: hello-app  # nome da imagem Docker

jobs:
  # Testa a aplicação
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4   # pega o código
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: python -c "from main import app; print('API OK')"

  # Build e push da imagem Docker
  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      - uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            ${{ secrets.DOCKER_USERNAME }}/${{ env.IMAGE_NAME }}:latest
            ${{ secrets.DOCKER_USERNAME }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

  # Atualiza os manifests do ArgoCD
  update-manifests:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          repository: gabrielMC6/app-manifest  # repo de manifests
          path: manifests
          ref: main
      - run: |
          cd manifests/manifests
          # atualiza a tag da imagem no deployment.yaml
          sed -i 's|gabrielMC6/hello-app:.*|gabrielMC6/hello-app:${{ github.sha }}|' deployment.yaml
      - uses: peter-evans/create-pull-request@v5
        with:
          token: ${{ secrets.MANIFESTS_TOKEN }}  # token para gravar no repo
          path: manifests
          commit-message: "ci: update to ${{ github.sha }}"
          title: "New image: ${{ github.sha }}"
          branch: update-${{ github.sha }}
          delete-branch: true
<img width="941" height="422" alt="secrets" src="https://github.com/user-attachments/assets/fd840676-d300-4240-88e7-d16a6d5b848b" />

