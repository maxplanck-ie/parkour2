FROM node:20-bookworm
WORKDIR /usr/src/app
EXPOSE 5173
CMD ["npm", "run", "start-dev"]
