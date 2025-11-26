FROM node:16-debian

RUN mkdir node

COPY . /node

WORKDIR /node

RUN npm install

EXPOSE 5000

CMD ["npm", "start"]