FROM node:25-bullseye
WORKDIR /usr/src/app
EXPOSE 5173
CMD ["npm", "run", "start-prod"]
