FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install
RUN npm install -D tailwindcss postcss autoprefixer
COPY . .
RUN npx tailwindcss init -p || true
RUN npm run build
RUN npm install -g serve

EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
