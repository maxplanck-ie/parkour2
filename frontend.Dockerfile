FROM node:25-bullseye AS pk2_base
WORKDIR /usr/src/app
EXPOSE 5173

FROM pk2_base AS pk2_dev
CMD ["npm", "run", "start-dev"]

FROM pk2_base AS pk2_lint
CMD ["npm", "run", "lint"]

FROM pk2_base AS pk2_prod
CMD ["npm", "run", "start-prod"]
