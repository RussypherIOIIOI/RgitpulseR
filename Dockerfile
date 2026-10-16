FROM node:24-bookworm-slim@sha256:a5f4366e834695d5f363b920c104953a535d3a9864d1bdf74566a0ebe01daee5 AS web
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts
COPY app ./app
COPY lib ./lib
COPY tsconfig.json next.config.mjs ./
RUN npm run build

FROM node:24-bookworm-slim@sha256:a5f4366e834695d5f363b920c104953a535d3a9864d1bdf74566a0ebe01daee5 AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts

FROM python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 gitpulse
WORKDIR /app
COPY --from=web /usr/local/bin/node /usr/local/bin/node
COPY pyproject.toml requirements.lock ./
COPY src ./src
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --require-hashes -r requirements.lock \
    && /opt/venv/bin/pip install --no-cache-dir --no-deps .
COPY --from=web --chown=gitpulse /app/.next ./.next
COPY --from=dependencies /app/node_modules ./node_modules
COPY --from=web /app/package.json ./package.json
COPY next.config.mjs ./next.config.mjs
COPY app/fonts/OFL.txt app/fonts/FONTLOG.txt ./licenses/MatrixSans/
COPY migrations ./migrations
COPY scripts/start-container.sh ./scripts/start-container.sh
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PATH="/opt/venv/bin:$PATH"
USER gitpulse
EXPOSE 3000
CMD ["sh", "scripts/start-container.sh"]
