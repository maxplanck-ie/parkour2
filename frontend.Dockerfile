FROM node:24-bullseye
WORKDIR /usr/src/app
COPY ./frontend/package.json ./frontend/package-lock.json* ./
RUN npm install
EXPOSE 5173
CMD ["npm", "run", "start-prod"]
