import express, { NextFunction, Response, Request } from 'express';
import bodyParser from 'body-parser';
import cors from 'cors';
import dotenv from 'dotenv'
import axios from 'axios';

dotenv.config();
const app = express();

app.use(cors());
app.use(bodyParser.json());

// CORS Headers => Required for cross-origin/ cross-server communication
app.use((req: Request, res: Response, next: NextFunction) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'Origin, X-Requested-With, Content-Type, Accept, Authorization'
  );
  res.setHeader(
    'Access-Control-Allow-Methods',
    'GET, POST, PATCH, DELETE, OPTIONS'
  );
  next();
});

const PORT = Number(process.env.NODE_ENV_PORT) | 5000
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
