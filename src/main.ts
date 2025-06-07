import { Server } from './Server';
import { createServer } from 'http';
import express, { Request, Response } from 'express';
import cors from 'cors';

const app = express();
const port = process.env.PORT || 3000;

// Add middleware
app.use(cors());
app.use(express.json());

// Create HTTP server
const httpServer = createServer(app);

// Create and configure MCP server
const server = new Server();
server.connect(new (require('./transport/stdio')).StdioServerTransport());

// Handle server closure
server.on('close', () => {
    httpServer.close();
});

// Start the server
httpServer.listen(port, () => {
    console.log(`Quran MCP server running on port ${port}`);
    server.start();
});