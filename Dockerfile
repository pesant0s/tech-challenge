# Stage 1: instala dependências em um virtualenv isolado
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN python -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: imagem de runtime enxuta
FROM python:3.12-slim

WORKDIR /app

# Cria usuário sem privilégios
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copia o venv completo (python + pacotes com shebangs corretos)
COPY --from=builder /venv /venv

# Copia o código da aplicação
COPY . .

# Garante que o usuário tem acesso ao diretório
RUN chown -R appuser:appgroup /app

USER appuser

ENV PATH=/venv/bin:$PATH
ENV PYTHONPATH=/app

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
