CI/CD com o GitHub Actions – DevSecOps

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


Após o build (docker build -t fastapi-ci-cd:latest .) e execução local (docker run -p 8000:80 fastapi-ci-cd), a aplicação respondeu corretamente em http://localhost:8000/ com {"message": "jacare"}.

Etapa 2 – Configuração do pipeline no GitHub Actions
1. Configuração dos Secrets

No repositório fastapi-ci-cd foram adicionados os seguintes secrets:

DOCKER_USERNAME → usuário Docker Hub

DOCKER_PASSWORD → token Docker Hub

MANIFESTS_TOKEN → token para gravar no repositório app-manifest

SSH_PRIVATE_KEY → chave privada (se usada em outro contexto)

2. Workflow CI/CD

O workflow .github/workflows/ci-cd.yaml automatiza teste, build e deploy, acionado a cada push na branch main.

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
  test: # testa aplicação
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: python -c "from main import app; print('API OK')"

  build-and-push: # build e push Docker
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

  update-manifests: # atualiza manifests ArgoCD
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

