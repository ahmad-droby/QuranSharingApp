export type Message = {
    action: string;
    data: any;
};

export class Client {
    id: string;
    ref: any;
    
    constructor(id: string, ref: any) {
        this.id = id;
        this.ref = ref;
    }
}

export abstract class Transport {
    abstract send(message: Message): void;
    abstract onMessage(callback: (message: Message) => void): void;
}

export class StdioServerTransport extends Transport {
    constructor() {
        super();
        // Initialize transport
        process.stdin.on('data', (data: Buffer) => {
            const message = JSON.parse(data.toString());
            this.onMessage(message);
        });
    }

    send(message: Message): void {
        process.stdout.write(JSON.stringify(message) + '\n');
    }

    onMessage(callback: (message: Message) => void): void {
        // Store callback for message handling
        this.callback = callback;
    }

    private callback: ((message: Message) => void) | null = null;
}

export class QuranService {
    private quranData: any;

    constructor() {
        // Load Quran data from file or resource
        const quranPath = require.resolve('./quran.json');
        this.quranData = require(quranPath);
    }

    public getVerse(surah: number, ayah: number): string {
        return this.quranData[surah][ayah];
    }

    public getQuranText(): string {
        return JSON.stringify(this.quranData);
    }
}

export class Server {
    private transport: Transport;
    private clients: Client[] = [];
    private quranService: QuranService;
    
    constructor() {
        this.quranService = new QuranService();
    }

    public connect(transport: Transport): void {
        this.transport = transport;
        this.setupMessageHandling();
    }

    private setupMessageHandling(): void {
        this.transport.onMessage((message: Message) => {
            switch (message.action) {
                case 'connect':
                    this.handleClientConnect(message);
                    break;
                case 'disconnect':
                    this.handleClientDisconnect(message);
                    break;
                case 'get_verse':
                    this.sendQuranVerse(message.data.surah, message.data.ayah);
                    break;
                default:
                    this.broadcast(message);
            }
        });
    }

    public start(): void {
        // Start the server
    }

    public on(event: string, callback: () => void): void {
        // Implement event listener logic
    }

    private handleClientConnect(message: Message): void {
        const client = new Client(message.data.clientId, message.data.ref);
        this.clients.push(client);
        console.log(`Client connected: ${client.id}`);
    }

    private handleClientDisconnect(message: Message): void {
        const clientId = message.data.clientId;
        this.clients = this.clients.filter(client => client.id !== clientId);
        console.log(`Client disconnected: ${clientId}`);
    }

    private broadcast(message: Message): void {
        this.clients.forEach(client => {
            this.transport.send({
                action: 'message',
                data: message.data
            });
        });
    }

    private sendQuranVerse(surah: number, ayah: number): void {
        const verse = this.quranService.getVerse(surah, ayah);
        this.broadcast({
            action: 'quran_verse',
            data: {
                surah,
                ayah,
                text: verse
            }
        });
    }
}