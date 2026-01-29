FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application code
COPY . .

# Build for production
# RUN npm run build

# Default command (development)
CMD ["npm", "run", "dev"]
