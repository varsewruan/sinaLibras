# Deploy SINALibras no Fly.io

Arquitetura: **uma única VM** servindo SPA + API no mesmo host (same-origin, sem CORS).
MongoDB: **Atlas free tier (M0)** — Fly.io não tem Mongo gerenciado.

---

## 1. MongoDB Atlas (5 minutos, grátis para sempre)

1. Crie conta em https://www.mongodb.com/cloud/atlas/register
2. **Build a Database** → **M0 FREE** → escolha região (use **AWS / São Paulo** se disponível, senão a mais próxima)
3. **Security → Database Access**: crie um usuário com senha forte. Anote.
4. **Security → Network Access**: clique **Add IP Address** → **Allow access from anywhere** (`0.0.0.0/0`)
   *Por que: Fly.io não publica faixa fixa de IPs. O acesso é protegido pelas credenciais.*
5. **Database → Connect → Drivers → Python**: copie a connection string. Exemplo:
   ```
   mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
   Substitua `<user>` e `<password>` pelos do passo 3. Guarde — vira o `MONGO_URL`.

---

## 2. Fly.io: instalar CLI + login

```powershell
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex
```

Depois:

```powershell
fly auth login           # abre o navegador
fly auth signup          # se ainda não tiver conta — pede cartão (não cobra na free)
```

---

## 3. Criar o app e configurar secrets

A partir da raiz do repo:

```powershell
# Cria o app no Fly usando o nome que está no fly.toml.
# --no-deploy: só registra; ainda não envia código.
# Se "sinalibras" estiver tomado, escolha outro nome e atualize a linha
# `app = "..."` no fly.toml.
fly apps create sinalibras

# Gera um JWT_SECRET aleatório e injeta tudo de uma vez.
$jwt = python -c "import secrets; print(secrets.token_urlsafe(48))"

fly secrets set `
  JWT_SECRET="$jwt" `
  MONGO_URL="mongodb+srv://USER:PASS@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority" `
  DB_NAME="sinalibras" `
  CORS_ORIGINS="https://sinalibras.fly.dev"
```

> **`CORS_ORIGINS`**: como SPA e API estão na mesma origem, CORS não é estritamente necessário, mas mantemos restrito ao domínio público por defesa em profundidade. Se você apontar domínio próprio depois, adicione: `CORS_ORIGINS="https://sinalibras.fly.dev,https://seusite.com"`.

---

## 4. Deploy

```powershell
fly deploy
```

O `fly.toml` já aponta para `Dockerfile.deploy`. O build roda em máquina remota do Fly (não consome sua banda). Saída esperada:

```
==> Building image
==> Pushing image to fly
==> Creating release
==> Monitoring deployment
 ✔ Machine d8911... is healthy
```

Acesse: https://sinalibras.fly.dev

---

## 5. Popular o banco (uma vez)

O seed roda dentro da própria VM via SSH:

```powershell
fly ssh console -C "python -m scripts.seed"
```

Saída esperada: `seeded 3 phases / 9 lessons / 36 signs`.

---

## 6. Operação diária

| Tarefa | Comando |
|---|---|
| Logs em tempo real | `fly logs` |
| Status da VM | `fly status` |
| Console na VM | `fly ssh console` |
| Reset do banco (CUIDADO) | `fly ssh console -C "python -m scripts.seed --reset"` |
| Atualizar secret | `fly secrets set CHAVE=valor` (re-deploy automático) |
| Rollback | `fly releases` e depois `fly deploy --image <imagem-anterior>` |

---

## 7. Custo esperado (free tier 2026)

- 3 VMs `shared-cpu-1x / 256–512mb` grátis enquanto o uso for baixo
- Tráfego: 160GB/mês grátis
- Atlas M0: 512MB de storage, grátis para sempre
- **Estimativa para alguns dezenas de usuários: $0/mês**

Se passar do free tier, o billing fica em ~$2-5/mês para uma VM rodando 24/7.

---

## 8. Próximos passos (opcional)

- **Domínio próprio**: `fly certs add app.seudominio.com` + CNAME para `sinalibras.fly.dev`
- **Sempre on** (sem cold start): mude `min_machines_running = 1` no `fly.toml`
- **Mais memória** (se OOM em pico): `memory = "1gb"` no `[[vm]]`
- **Backups Atlas**: configurar via UI do Atlas (M0 não inclui backup automático — exportar via `mongodump` periodicamente)
