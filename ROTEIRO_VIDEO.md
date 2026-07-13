# 🎬 Roteiro do Vídeo — Tech Challenge Fase 02 (≤ 15 min)

Oficina Mecânica API · Arquitetura Hexagonal + Kubernetes + Terraform + CI/CD

Este documento tem **duas partes**:
- **Parte 0 — Conceitos**: um glossário em português simples. Leia uma vez para entender o vocabulário. *Não precisa falar isso no vídeo* — é só pra você dominar o assunto.
- **Roteiro**: o passo a passo cronometrado, com **o que dizer**, **os comandos** e, embaixo de cada comando, um bloco **🔍 O que isso faz** explicando em linguagem de leigo.

O vídeo **precisa** demonstrar 4 coisas (exigência do enunciado):
1. **Deploy** da aplicação 2. **Execução do CI/CD** 3. **Consumo das APIs** 4. **Escalabilidade automática** (HPA)

---

# 📚 PARTE 0 — Conceitos em linguagem de leigo

Pense na aplicação como um **restaurante**:

| Termo | O que é, em português simples |
|---|---|
| **Docker** | Programa que empacota sua aplicação numa "caixa" fechada (com Python, bibliotecas, tudo dentro) que roda igual em qualquer computador. Essa caixa é a **imagem**. |
| **Imagem** | O "molde congelado" da aplicação (o cardápio + a cozinha montada). A partir dela criam-se cópias que rodam. |
| **Container** | Uma **cópia rodando** da imagem (um prato sendo servido). Você pode ter vários containers iguais ao mesmo tempo. |
| **Docker Desktop** | O programa no seu Mac que faz o Docker funcionar. Precisa estar **aberto** para tudo abaixo funcionar. |
| **Kubernetes (K8s)** | O "gerente do restaurante": decide quantas cópias da aplicação rodam, reinicia as que caem, distribui a carga. É um **orquestrador de containers**. |
| **minikube** | Um Kubernetes **de mentirinha, na sua máquina** — um restaurante inteiro dentro do seu Mac, pra você testar sem precisar da nuvem. |
| **Pod** | A menor unidade do Kubernetes: uma "mesa" que roda um (ou poucos) container(s). Cada cópia da sua API roda num pod. |
| **Deployment** | A "receita" que diz ao Kubernetes: *"quero 2 cópias da API sempre no ar; se uma cair, sobe outra"*. |
| **Réplica** | Cada cópia idêntica da aplicação. 2 réplicas = 2 pods rodando a mesma API. |
| **Service (NodePort)** | A "recepção" com um telefone fixo: um endereço estável para acessar a API, mesmo que os pods por trás mudem. **NodePort** = expõe numa porta fixa (aqui, `30080`). |
| **ConfigMap** | Um "quadro de avisos" com configurações **não sensíveis** (ex.: nome do admin, origens de CORS). |
| **Secret** | Igual ao ConfigMap, mas para dados **sensíveis** (senhas, tokens). Fica separado por segurança. |
| **HPA** (Horizontal Pod Autoscaler) | O "gerente que contrata garçom extra na hora do rush": aumenta as réplicas automaticamente quando a CPU sobe, e reduz quando acalma. |
| **Migrations / Alembic** | Scripts que criam/atualizam as tabelas do banco de dados. Rodam automaticamente quando a aplicação sobe (`alembic upgrade head`). |
| **Terraform** | Ferramenta de "infraestrutura como código": em vez de clicar em botões, você **descreve a infra num arquivo** e ela é criada sozinha. |
| **CI/CD** | Esteira automática: a cada envio de código, ela **testa**, **empacota** e **entrega** a aplicação sem ninguém fazer à mão. CI = Integração Contínua, CD = Entrega Contínua. |
| **GitHub Actions** | A ferramenta que roda essa esteira dentro do GitHub. |
| **Registry / GHCR** | Um "armazém de imagens Docker" na internet. **GHCR** = o armazém do GitHub. |
| **kubectl** | O comando pelo qual você conversa com o Kubernetes ("mostre os pods", "aplique essa receita"). Lê-se "kube-control". |

> **Regra de ouro do minikube:** ele tem o **Docker dele, separado** do Docker do seu Mac. Uma imagem que você builda no Mac **não aparece** automaticamente lá dentro. Por isso a gente builda a imagem *dentro* do minikube (explicado na Preparação).

---

# ✅ PREPARAÇÃO (faça ANTES de gravar — não grave isto)

O objetivo é deixar tudo no ar antes de ligar a gravação, pra não gravar tempo morto.

### Passo 0 — Ligar o Docker (macOS)
```bash
open -a Docker
until docker info >/dev/null 2>&1; do sleep 2; done; echo "Docker pronto"
```
> **🔍 O que isso faz:** `open -a Docker` abre o Docker Desktop. A segunda linha é um "loop de espera": ela fica testando (`docker info`) a cada 2 segundos até o Docker responder, e só então escreve "Docker pronto". Necessário porque o Docker leva ~30-60s pra iniciar, e o minikube não sobe sem ele.

### Passo 1 — Subir o Kubernetes local
```bash
minikube start
minikube addons enable metrics-server
```
> **🔍 O que isso faz:** `minikube start` liga o cluster Kubernetes na sua máquina (usando o Docker como base). `metrics-server` é um "medidor de consumo": sem ele, o HPA não consegue ver o uso de CPU e **não escala** — por isso é obrigatório para a demo de escalabilidade.

### Passo 2 — Buildar a imagem DENTRO do minikube ⚠️ (o passo que mais confunde)
```bash
eval $(minikube docker-env)                    # aponta o docker pro minikube
docker build -t tech-challenge-api:latest .    # constrói a imagem lá dentro
docker images | grep tech-challenge-api        # confirma que ficou lá
```
> **🔍 O que isso faz:**
> - `eval $(minikube docker-env)` — este é o pulo do gato. Ele "redireciona" o seu comando `docker` para falar com o **Docker de dentro do minikube**, em vez do Docker do seu Mac. Vale **só para esse terminal**.
> - `docker build -t tech-challenge-api:latest .` — lê o `Dockerfile` e constrói a imagem da aplicação com o nome `tech-challenge-api:latest`. O `.` (ponto) no fim significa "use a pasta atual como material de construção". O nome tem que ser **exatamente** esse, porque é o que o `deployment.yaml` procura.
> - **Por quê dentro do minikube?** Porque o `deployment.yaml` usa `imagePullPolicy: Never` — que quer dizer *"nunca baixe da internet, use só a imagem que já está no nó"*. Se a imagem não estiver dentro do minikube, você vê o erro `ErrImageNeverPull` (ver Troubleshooting no fim).

### Passo 3 — Preparar as janelas e a ferramenta de carga
- Deixe 3 terminais abertos: **A** (comandos), **B** (`watch` dos pods), **C** (gerador de carga).
- Instale o gerador de carga: `brew install hey` (ou use o `ab`, que já vem no Mac).
- Confira que o último run do **GitHub Actions** está verde (aba Actions do repo).

**Checklist antes do REC:** Docker aberto · `minikube status` tudo *Running* · imagem no minikube · `kubectl top nodes` responde · Swagger abrindo.

---

# 🎥 BLOCO 1 — Abertura & Arquitetura · ⏱️ 0:00 – 1:30

**Mostrar:** o arquivo `arquitetura.excalidraw` (diagrama Hexagonal + diagrama Infra & Deploy).

**O que dizer:**
> "Olá! Este é o Tech Challenge da Fase 2 — a evolução do sistema de gestão de ordens de serviço de uma oficina mecânica. Refatoramos para **Arquitetura Hexagonal**, com o **domínio 100% puro** — as regras de negócio não dependem de framework nem de banco. Aqui está o diagrama hexagonal: adapters de entrada (HTTP), a camada de aplicação com os casos de uso, o domínio no centro, e os adapters de saída — banco e notificação. E aqui embaixo, o diagrama de **infraestrutura e fluxo de deploy**, que é o que vou demonstrar agora."

---

# 🎥 BLOCO 2 — Deploy da aplicação · ⏱️ 1:30 – 4:30

**Mostrar:** Terminal A aplicando os manifestos + Terminal B com os pods subindo.

> "Vou fazer o deploy no Kubernetes aplicando os manifestos da pasta `/k8s`."

```bash
kubectl apply -f k8s/namespace.yaml     # cria um "cômodo" isolado chamado 'oficina'
kubectl apply -f k8s/postgres/          # sobe o banco PostgreSQL com disco persistente
kubectl apply -f k8s/configmap.yaml     # configurações não sensíveis
kubectl apply -f k8s/secret.yaml        # senhas e tokens (ex.: token do webhook de e-mail)
kubectl apply -f k8s/deployment.yaml    # a API, com 2 réplicas
kubectl apply -f k8s/service.yaml        # o endereço fixo de acesso (porta 30080)
kubectl apply -f k8s/hpa.yaml            # o auto-escalador (2 a 5 réplicas)
```
> **🔍 O que isso faz:** `kubectl apply -f <arquivo>` entrega uma "receita" (arquivo YAML) para o Kubernetes e diz *"faça a realidade ficar assim"*. Cada linha cria uma peça:
> - `namespace` — um espaço isolado chamado `oficina` (como uma pasta) pra não misturar com outras coisas do cluster.
> - `postgres/` — a pasta inteira do banco: o banco em si (StatefulSet), o disco que guarda os dados mesmo se o pod reiniciar (PVC) e o endereço interno dele.
> - `configmap`/`secret` — as configurações e os segredos que a API vai ler.
> - `deployment` — pede 2 cópias da API rodando.
> - `service` — cria o "telefone fixo" (porta 30080) pra acessar a API de fora.
> - `hpa` — liga o auto-escalonamento por CPU.

```bash
kubectl get pods -n oficina -w
```
> **🔍 O que isso faz:** `get pods` lista as "mesas" (pods) rodando. `-n oficina` = só no nosso espaço. `-w` (watch) = **fica atualizando na tela** conforme os pods mudam de estado (ContainerCreating → Running). Deixe rodando no Terminal B pra mostrar os pods nascendo.

```bash
kubectl logs deploy/tech-challenge-api -n oficina | head -20
```
> **🔍 O que isso faz:** mostra o **log** (as mensagens) da aplicação. Aqui você vê o `alembic upgrade head` criando as tabelas do banco e depois o Uvicorn (servidor web) subindo. É a prova de que o banco foi configurado sozinho no boot.

```bash
export URL=$(minikube service tech-challenge-svc -n oficina --url)
curl -s $URL/health
```
> **🔍 O que isso faz:** `minikube service ... --url` descobre o endereço completo de acesso à API e guarda na variável `URL`. `curl -s $URL/health` faz uma chamada de teste no endpoint de saúde — deve responder `{"status":"ok"}`, provando que a API está no ar.

**(Opcional) Terraform — mostrar que a infra também é código:**
```bash
cd infra && terraform init && terraform plan && cd ..
```
> **🔍 O que isso faz:** `terraform init` prepara a pasta (baixa os "plugins"). `terraform plan` mostra **o que seria criado** (namespace, deployment, service, HPA, banco...) **sem criar de fato** — é um "preview". Serve pra dizer no vídeo: "toda essa infra está descrita como código, inclusive o banco".

---

# 🎥 BLOCO 3 — Execução do CI/CD · ⏱️ 4:30 – 6:30

**Mostrar:** aba **Actions** do repositório no GitHub (no navegador).

**O que dizer:**
> "A esteira de CI/CD está no arquivo `.github/workflows/ci.yml`. Todo envio de código pro GitHub dispara ela automaticamente."

Abra um run verde e mostre os 3 jobs:
> "O primeiro job, **test**, instala tudo, roda os **102 testes automatizados** e ainda valida os manifestos do Kubernetes. Passando, na branch principal roda o **deploy-k8s**: ele cria um Kubernetes de verdade dentro da esteira, aplica os manifestos e testa o `/health` — ou seja, o deploy é validado a cada entrega. Por fim, o **build-and-push** empacota a imagem Docker e publica no repositório de imagens do GitHub, o GHCR."

> **🔍 Conceito pro vídeo:** "job" é uma etapa da esteira. Elas rodam em sequência: se os testes falham, nada é publicado — isso evita subir código quebrado pra produção.

---

# 🎥 BLOCO 4 — Consumo das APIs · ⏱️ 6:30 – 11:00

**Mostrar:** o **Swagger** aberto em `$URL/docs` (documentação interativa da API).
> **🔍 O que é Swagger:** uma página web, gerada automaticamente, que lista todos os endpoints e deixa você **testar cada um clicando** ("Try it out"), sem precisar de outro programa.

**Passo a passo (no Swagger):**

1. **Login** — `POST /auth/token` (`admin` / `admin123`) → copie o `access_token`, clique em **Authorize** e cole.
   > **🔍 O que faz:** troca usuário/senha por um **token JWT** — um "crachá temporário" que autoriza as próximas chamadas. Sem ele, os endpoints protegidos respondem 401.

2. **Cadastros** — crie os dados base:
   - `POST /cadastro/clientes` → `{"nome":"Ana Silva","cpf_cnpj":"529.982.247-25","telefone":"11999998888","email":"ana@exemplo.com"}`
   - `POST /cadastro/veiculos` → placa `ABC-1234` + `cliente_id`
   - `POST /catalogo/servicos` → `{"nome":"Revisão completa","preco":250.00}`
   - `POST /estoque/pecas` → `{"nome":"Filtro de óleo","preco":50.0,"quantidade":10,"estoque_minimo":2}`
   > **🔍 O que faz:** cadastra cliente, veículo, um serviço e uma peça em estoque — os ingredientes pra montar uma ordem de serviço. Repare que o CPF é validado de verdade (dígitos verificadores).

3. **Abrir a OS** — `POST /atendimento/os` com o serviço + a peça. **Guarde o `id` retornado.**
   > **🔍 O que faz:** cria a Ordem de Serviço, devolve o **identificador único** e o status inicial **AGUARDANDO_APROVACAO**, com o orçamento **calculado automaticamente** (soma serviços + peças).

4. **E-mail de aprovação (a porta de saída)** — no Terminal A:
   ```bash
   kubectl logs -l app=tech-challenge-api -n oficina --tail=50 | grep SIMULADO
   ```
   > **🔍 O que faz:** `-l app=tech-challenge-api` pega os logs de **todos os pods** da API (não só um). `grep SIMULADO` filtra só a linha do e-mail. Deve aparecer o `📧 [E-MAIL SIMULADO] ... aguardando aprovação`.
   > **O que dizer:** "Ao abrir a OS, o sistema dispara um e-mail de aprovação pro cliente. Estamos usando um adapter **simulado** que escreve no log — mas, graças à arquitetura de portas e adapters, trocar por um provedor real como SendGrid ou AWS SES seria só criar outro adapter, **sem mudar a regra de negócio**."

5. **Aprovar via webhook** — `POST /webhooks/email`:
   ```json
   {"os_id":"<ID_DA_OS>","acao":"APROVAR","cpf_cnpj":"529.982.247-25","token":"webhook-secret-local"}
   ```
   > **🔍 O que faz:** simula o clique do cliente em "Aprovar" no e-mail. O serviço de e-mail chamaria este endpoint. Ele confere o `token` (comparação segura contra ataques de tempo) e muda o status pra **RECEBIDA**.

6. **Avançar o status** — `PATCH /atendimento/os/{id}/status`: `EM_DIAGNOSTICO` → `EM_EXECUCAO` → `FINALIZADA`.
   > **🔍 O que faz:** move a OS pela "esteira de produção" da oficina. Ao entrar em **EM_EXECUCAO**, as peças são **baixadas do estoque automaticamente** — mostre em `GET /estoque/pecas/{id}` que a quantidade caiu de 10 pra 9.

7. **Fila priorizada** — `GET /atendimento/os/fila`.
   > **🔍 O que faz:** lista as OS ativas ordenadas por prioridade (Em Execução > Aguardando > Diagnóstico > Recebida), mais antigas primeiro, escondendo as finalizadas/entregues — exatamente como o enunciado pede.

---

# 🎥 BLOCO 5 — Escalabilidade automática (HPA) · ⏱️ 11:00 – 14:00

**Mostrar:** Terminal B com o HPA/pods; Terminal C gerando carga.

> "Configuramos um auto-escalador que mantém de 2 a 5 cópias da API, criando mais quando a CPU passa de 70%."

```bash
kubectl get hpa -n oficina -w
```
> **🔍 O que faz:** mostra o auto-escalador em tempo real: uso atual de CPU vs. alvo (70%) e quantas réplicas existem. Deixe rodando pra ver os números mudarem.

```bash
# Terminal C — dispara o "pico de acesso"
hey -z 90s -c 60 $URL/health
#   alternativa (já vem no Mac): ab -n 200000 -c 60 $URL/health
```
> **🔍 O que faz:** `hey` bombardeia a API com muitos acessos ao mesmo tempo. `-z 90s` = por 90 segundos; `-c 60` = 60 conexões simultâneas. Isso força a CPU a subir, simulando um horário de pico da oficina. (O enunciado permite explicitamente **simular** carga.)

```bash
kubectl get pods -n oficina -w
```
> **🔍 O que faz:** enquanto a carga roda, observe o Kubernetes **criando novos pods sozinho** (de 2 → 3 → 4 → 5). Essa é a demonstração central da escalabilidade. Ao parar a carga (Ctrl+C), depois de alguns minutos ele reduz de volta pra 2, economizando recursos.

> ⚠️ **Se o HPA demorar a escalar:** aumente pra `-c 100`, ou — só pra demo — abra `k8s/hpa.yaml`, troque `averageUtilization: 70` por `40`, rode `kubectl apply -f k8s/hpa.yaml` e teste de novo.

---

# 🎥 BLOCO 6 — Encerramento · ⏱️ 14:00 – 15:00

> "Recapitulando a Fase 2: refatoramos pra **Arquitetura Hexagonal com domínio puro** e Clean Code; **102 testes automatizados**; aplicação **containerizada** com Docker; **orquestração no Kubernetes** com Deployment, Services, ConfigMap, Secret e HPA; **infraestrutura como código** em Terraform provisionando cluster e banco; e uma **pipeline de CI/CD** que testa, faz deploy e publica a imagem. Obrigado!"

---

# 🩺 TROUBLESHOOTING (erros comuns e como resolver)

**`Unable to pick a default driver ... docker: Not healthy`** (no `minikube start`)
→ O Docker Desktop está **fechado**. Abra ele (`open -a Docker`), espere ficar pronto e rode o `minikube start` de novo.

**`ErrImageNeverPull`** (pod não inicia) — *este foi o que você pegou*
→ A imagem não está dentro do minikube. Como o deployment usa `imagePullPolicy: Never`, ela precisa ser buildada lá dentro:
```bash
eval $(minikube docker-env)
docker build -t tech-challenge-api:latest .
kubectl rollout restart deployment/tech-challenge-api -n oficina   # faz os pods pegarem a imagem nova
kubectl rollout status deployment/tech-challenge-api -n oficina
```
> **🔍 Por quê:** cada terminal novo volta a apontar pro Docker do Mac. Sempre rode `eval $(minikube docker-env)` **no mesmo terminal** antes de buildar. O `rollout restart` recria os pods pra usarem a imagem recém-criada.

**`ImagePullBackOff`**
→ Kubernetes tentou baixar a imagem de um registry e não achou. Mesmo remédio acima (buildar local) — ou confirmar o nome da imagem no `deployment.yaml`.

**`CrashLoopBackOff`** (pod sobe e cai em loop)
→ A aplicação está quebrando no boot. Veja o motivo: `kubectl logs <nome-do-pod> -n oficina`. Costuma ser variável de ambiente/secret faltando ou banco indisponível.

**HPA mostra `<unknown>` em CPU**
→ O `metrics-server` não está ativo. Rode `minikube addons enable metrics-server` e espere ~1 min.

**`kubectl` não encontra nada / "connection refused"**
→ O minikube não está rodando. Cheque com `minikube status`; se preciso, `minikube start`.

---

# 🔑 Dados úteis durante a gravação
| Item | Valor |
|---|---|
| Admin | `admin` / `admin123` |
| CPF de teste (válido) | `529.982.247-25` |
| Token do webhook | `webhook-secret-local` |
| URL da API | `minikube service tech-challenge-svc -n oficina --url` |
| Swagger | `<URL>/docs` |
| Namespace | `oficina` |

# 📋 Checklist final antes de publicar
- [ ] Vídeo ≤ 15 minutos, no YouTube/Vimeo (público ou **não listado**)
- [ ] Mostrou: deploy · CI/CD · consumo das APIs · escalabilidade (HPA)
- [ ] Áudio audível, fonte do terminal grande e legível
- [ ] Link do vídeo copiado para o README.md e para o PDF de submissão
