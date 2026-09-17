FROM node:22-alpine

RUN apk add --no-cache libc6-compat

WORKDIR /workspace/uis

COPY healthcore/package.json healthcore/package-lock.json ./healthcore/
COPY backoffice/package.json backoffice/package-lock.json ./backoffice/
RUN cd healthcore && npm ci
RUN cd backoffice && npm ci

COPY start.sh /workspace/uis/start.sh
RUN sed -i 's/\r$//' /workspace/uis/start.sh && chmod +x /workspace/uis/start.sh

EXPOSE 3000 3001

CMD ["/workspace/uis/start.sh"]
