FROM node:24-bullseye
WORKDIR /usr/src/app
EXPOSE 5173
CMD ["npm", "run", "start-prod"]
