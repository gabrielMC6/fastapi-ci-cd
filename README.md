CI/CD com GitHub Actions – DevSecOps

Aluno: Gabriel de Mendonça Costa

Objetivo

Automatizar todo o ciclo de desenvolvimento, build e deploy de uma aplicação FastAPI, usando GitHub Actions, Docker Hub e ArgoCD em um ambiente Kubernetes local com Rancher Desktop.

Pré-requisitos

Conta no GitHub (repositório público)

Conta no Docker Hub com token de acesso

Rancher Desktop com Kubernetes habilitado

kubectl configurado corretamente (kubectl get nodes)

ArgoCD instalado no cluster local

Git instalado

Python 3 e Docker instalados

Etapa 1 – Criação da aplicação e repositórios

Foram criados dois repositórios públicos:

fastapi-ci-cd: contém a aplicação, Dockerfile, requirements.txt e workflow do GitHub Actions.

app-manifest: contém os arquivos de manifesto Kubernetes (deployment.yaml e service.yaml), monitorados pelo ArgoCD.

Aplicação FastAPI (main.py)
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "jacare"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

Dependências (requirements.txt)
fastapi==0.104.1
uvicorn==0.24.0

Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]


Teste local:
Build: docker build -t fastapi-ci-cd:latest .
Run: docker run -p 8000:80 fastapi-ci-cd
Acesse: http://localhost:8000/ → {"message": "jacare"}

Etapa 2 – Configuração do pipeline no GitHub Actions
1. Configuração dos Secrets

No repositório fastapi-ci-cd, adicione os seguintes Secrets:

DOCKER_USERNAME → usuário Docker Hub

DOCKER_PASSWORD → token Docker Hub

MANIFESTS_TOKEN → token para gravar no repositório app-manifest

SSH_PRIVATE_KEY → chave privada (opcional, caso use SSH)

2. Workflow CI/CD

O workflow .github/workflows/ci-cd.yaml automatiza:

Testes da aplicação

Build e push da imagem Docker

Atualização dos manifests do ArgoCD

Acionamento: a cada push na branch main.

name: CI/CD Pipeline

permissions:
  contents: write
  pull-requests: write

on:
  push:
    branches: [ main ]

env:
  IMAGE_NAME: hello-app

jobs:
  # Etapa 1: Testar aplicação
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: python -c "from main import app; print('API OK')"

  # Etapa 2: Build e push da imagem Docker
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

  # Etapa 3: Atualização dos manifests
  update-manifests:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          repository: gabrielMC6/app-manifest
          path: manifests
          ref: main

      - name: Update image tag
        run: |
          cd manifests/manifests
          sed -i 's|gabrieldemendoncacosta/hello-app:.*|gabrieldemendoncacosta/hello-app:${{ github.sha }}|' deployment.yaml

      - uses: peter-evans/create-pull-request@v5
        with:
          token: ${{ secrets.MANIFESTS_TOKEN }}
          path: manifests
          commit-message: "ci: update to ${{ github.sha }}"
          title: "New image: ${{ github.sha }}"
          branch: update-${{ github.sha }}
          delete-branch: true
