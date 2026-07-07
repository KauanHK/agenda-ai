# Design: Separação de rotas Users — global vs. estabelecimento

**Data:** 2026-05-15

## Contexto

O router de users (`/users/...`) acumulou rotas de responsabilidades distintas: gerenciamento global de usuários e gerenciamento de membros por estabelecimento. O objetivo é separar essas responsabilidades de forma clara.

## Rotas finais

### Globais — `/users/...`
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/users/me` | Perfil do usuário autenticado |
| PATCH | `/users/me` | Atualiza próprio perfil |
| GET | `/users/` | Lista todos os usuários (global admin) |
| GET | `/users/{user_id}` | Busca usuário por ID |
| POST | `/users/` | Cria usuário |
| PATCH | `/users/{user_id}` | Atualiza usuário |
| DELETE | `/users/{user_id}` | Remove usuário |
| POST | `/users/{user_id}/activate` | Ativa usuário globalmente (`user.is_active = True`) |
| POST | `/users/{user_id}/deactivate` | Desativa usuário globalmente (`user.is_active = False`) |

### Por estabelecimento — `/establishments/{establishment_id}/members/...`
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/establishments/{id}/members/` | Lista membros do estabelecimento |
| POST | `/establishments/{id}/members/` | Adiciona membro ao estabelecimento |
| GET | `/establishments/{id}/members/{user_id}` | Busca membro específico *(novo)* |
| PATCH | `/establishments/{id}/members/{user_id}` | Atualiza dados do membro (role, etc.) |
| DELETE | `/establishments/{id}/members/{user_id}` | Remove membro do estabelecimento |
| POST | `/establishments/{id}/members/{user_id}/activate` | Ativa membro no estabelecimento (`membership.is_active = True`) *(novo)* |
| POST | `/establishments/{id}/members/{user_id}/deactivate` | Desativa membro no estabelecimento (`membership.is_active = False`) *(novo)* |

## Mudanças

### 1. Model `Membership` — novo campo
```python
is_active: Mapped[bool] = mapped_column(default=True, server_default="true", nullable=False)
```
Seguido de migration `alembic revision --autogenerate`.

`MembershipRead` e `MembershipReadExpanded` passam a expor `is_active`.

### 2. Novo use case: `MembershipActivator`
Arquivo: `app/modules/memberships/application/activate.py`

- `activate(user_id, establishment_id, actor)` → `membership.is_active = True`
- `deactivate(user_id, establishment_id, actor)` → `membership.is_active = False`

Autorização: apenas `establishment_admin` do estabelecimento ou `global_admin`, via `_authz.py` existente.

`MembershipActivatorDep` adicionado em `app/modules/memberships/api/deps.py`.

### 3. Memberships router — 3 endpoints novos
- `GET /{establishment_id}/members/{user_id}` → `MembershipReadExpanded`
- `POST /{establishment_id}/members/{user_id}/activate` → `MembershipRead`
- `POST /{establishment_id}/members/{user_id}/deactivate` → `MembershipRead`

### 4. Users router — 1 rota removida
- `GET /users/establishments/{establishment_id}/members` removida: era duplicata do `GET /establishments/{establishment_id}/members/` do memberships router, e retornava `UserRead` em vez de `MembershipRead`, gerando inconsistência.

## O que NÃO muda
- Rotas globais de users permanecem intactas
- Lógica de authorização existente no módulo memberships
- Módulo users não ganha dependência do módulo memberships
