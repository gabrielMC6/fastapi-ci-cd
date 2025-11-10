# CI/CD com o GitHub Actions – DevSecOps

## Objetivo
Automatizar todo o ciclo de desenvolvimento, build e deploy de 
uma aplicação FastAPI, usando GitHub Actions, Docker Hub e 
ArgoCD em um ambiente Kubernetes local configurado com 
Rancher Desktop.

## Pré-requisitos
- Conta no GitHub (repositório público)
- Conta no Docker Hub com token de acesso
- Rancher Desktop com Kubernetes habilitado
- kubectl configurado corretamente (kubectl get nodes)
- ArgoCD instalado no cluster local
- Git instalado
- Python 3 e Docker instalados

---

## Etapa 1 – Criação da aplicação e repositórios

**Repositórios criados:**
- **fastapi-ci-cd**: Aplicação + Dockerfile + GitHub Actions
- **app-manifest**: Manifests Kubernetes para ArgoCD

**Aplicação FastAPI (main.py):**

<img width="319" height="269" alt="JACARE" src="https://github.com/user-attachments/assets/5c8ed112-f2df-4140-848f-f264ba4ec89b" />

**dockerfile:**
<img width="428" height="267" alt="dockerfile" src="https://github.com/user-attachments/assets/f8ec9927-c6bf-48ac-89bc-2b8a035f24dc" />

**Etapa 2 – Configuração do pipeline no GitHub Actions**
**Configuração dos Secrets**

No repositório fastapi-ci-cd foram adicionados os seguintes secrets:

DOCKER_USERNAME → usuário Docker Hub

DOCKER_PASSWORD → token Docker Hub

MANIFESTS_TOKEN → token para gravar no repositório app-manifest

SSH_PRIVATE_KEY → chave privada
<img width="941" height="422" alt="secrets" src="https://github.com/user-attachments/assets/7a706121-f649-4b5c-983a-e6b31f347515" />

**Criar Workflow:**

### Workflow – `.github/workflows/ci-cd.yaml`
```yaml
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
```

### 3 – Manifests Kubernetes para ArgoCD

**Objetivo:**  
Criar os manifests de *Deployment*,*application* e *Service* no repositório `app-manifest` para que o ArgoCD sincronize o deploy automaticamente.

**Arquivos criados em `app-manifest/manifests/`:**


-<img width="295" height="295" alt="deploy" src="https://github.com/user-attachments/assets/ef400529-68c1-4933-824d-e6063e9540b3" />

<img width="295" height="295" alt="aplica" src="https://github.com/user-attachments/assets/9056cf8f-07f9-4dbe-a327-f4cfa45faf5a" />

<img width="239" height="262" alt="service" src="https://github.com/user-attachments/assets/0f0c029b-bf9d-47bb-ba54-cc8b20b83140" />



Esses arquivos são a **fonte de verdade** que o ArgoCD monitora. O pipeline atualiza a tag no `deployment.yaml` e cria um PR; o ArgoCD aplica a alteração após o merge/sync.

## Etapa 4 – Configuração do ArgoCD

**Objetivo:**
Instalar e configurar o ArgoCD no cluster Kubernetes para 
automatizar o deploy baseado nos manifests do Git.

**Instalação:**
kubectl create namespace argocd


kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# acessar interface:
kubectl port-forward svc/argocd-server -n argocd 8080:443

Acessar o argocd pelo Localhost:8080.


**configurar argoCD**
<img width="941" height="395" alt="argohelloapp" src="https://github.com/user-attachments/assets/bbe1bda2-d6b3-4d42-9266-904401c84899" />   

## Etapa 5 – Testes e Validação  

Esta etapa teve como objetivo confirmar o funcionamento completo do pipeline **CI/CD** e garantir que a aplicação estivesse respondendo corretamente após o deploy no **Kubernetes**.  

Com o **ArgoCD** sincronizado, foi realizado o redirecionamento de porta para acesso local ao serviço:  


kubectl port-forward svc/hello-app-service 8081:80

<img width="407" height="245" alt="jacareapi" src="https://github.com/user-attachments/assets/ebc09ec1-bcb2-48ef-9a91-61c42a117887" />

**Atualizar main**


<img width="578" height="398" alt="novomain" src="https://github.com/user-attachments/assets/2704ef9d-d3b0-4bd8-be1c-9a2c24a1cd16" />


**Observar Workflow**



<img width="671" height="203" alt="workflow" src="https://github.com/user-attachments/assets/8f62f7db-5aa4-4cb1-84c9-d2839963abfa" />


**Depois de aprovar o pull request você deve dar refresh no argoCd e pronto**

<img width="1322" height="203" alt="Captura de tela 2025-11-09 223641" src="https://github.com/user-attachments/assets/4c8a0ff2-4b17-4a89-81ca-33ce5ab2aec0" />





