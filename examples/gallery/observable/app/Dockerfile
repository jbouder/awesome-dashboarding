FROM node:22.21.1-bookworm-slim
ENV NODE_ENV=production OBSERVABLE_TELEMETRY_DISABLE=true PORT=3000
WORKDIR /home/node/app
COPY --chown=node package.json package-lock.json ./
RUN npm ci --omit=dev --no-audit --no-fund && npm cache clean --force
COPY --chown=node . .
RUN chmod +x start.sh && chown node /home/node/app
USER node
# Fill Framework's npm cache now, so a start without internet still builds.
# The data loaders fail here on purpose: the warehouse is not reachable yet.
RUN WAREHOUSE_URL= npx observable build > /dev/null 2>&1 || true
EXPOSE 3000
CMD ["./start.sh"]
